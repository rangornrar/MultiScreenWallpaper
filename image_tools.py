# image_tools.py
import copy
import json
import math
import os
import random
import time

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

PROXY_MAX_SIZE = 1024
PROJECT_SCHEMA_VERSION = 1


def open_image_upright(path):
    """Ouvre une image et applique l'orientation EXIF (photos de smartphone)."""
    with Image.open(path) as im:
        im.load()
        return ImageOps.exif_transpose(im)


class LoadedImage:
    """
    Optimisation mémoire et performance :
    - low_res_image (proxy, 1024 px max) : affichage temps réel dans Tkinter.
    - original_image : rechargé depuis le disque à la demande, pour l'export HD.
      Une image qui ne vient pas d'un fichier (tests, collage) reste en mémoire.
    """
    __slots__ = (
        "path", "_original", "original_size", "low_res_image", "display_image",
        "x", "y", "w", "h",
        "angle", "crop_box_norm",
        "brightness", "contrast", "saturation", "blur",
        "_preview_cache", "_aspect", "z_index"
    )

    def __init__(self, path, image: Image.Image):
        self.path = path
        rgba = image.convert("RGBA")
        self.original_size = rgba.size

        # Création du PROXY
        self.low_res_image = rgba.copy()
        self.low_res_image.thumbnail((PROXY_MAX_SIZE, PROXY_MAX_SIZE), Image.Resampling.LANCZOS)
        self.display_image = self.low_res_image

        # L'original n'est gardé en RAM que s'il ne peut pas être relu depuis le disque.
        self._original = None if self._can_reload() else rgba

        self.x = 0; self.y = 0; self.w = None; self.h = None
        self.angle = 0; self.z_index = 0
        self.crop_box_norm = (0.0, 0.0, 1.0, 1.0)

        self.brightness = 1.0; self.contrast = 1.0
        self.saturation = 1.0; self.blur = 0.0

        self._preview_cache = {}
        iw, ih = self.original_size
        self._aspect = (iw / ih) if ih else 1.0

    def _can_reload(self):
        return isinstance(self.path, str) and os.path.isfile(self.path)

    @property
    def original_image(self):
        if self._original is not None:
            return self._original
        return open_image_upright(self.path).convert("RGBA")

    def clone(self):
        # Clone optimisé (références partagées pour images lourdes)
        new_obj = LoadedImage.__new__(LoadedImage)
        new_obj.path = self.path
        new_obj._original = self._original
        new_obj.original_size = self.original_size
        new_obj.low_res_image = self.low_res_image

        if self.display_image is self.low_res_image:
            new_obj.display_image = new_obj.low_res_image
        else:
            new_obj.display_image = self.display_image.copy()

        new_obj.x = self.x; new_obj.y = self.y; new_obj.w = self.w; new_obj.h = self.h
        new_obj.angle = self.angle; new_obj.z_index = self.z_index
        new_obj.crop_box_norm = self.crop_box_norm
        new_obj.brightness = self.brightness; new_obj.contrast = self.contrast
        new_obj.saturation = self.saturation; new_obj.blur = self.blur
        new_obj._preview_cache = {}
        new_obj._aspect = self._aspect
        return new_obj

    def apply_filters(self, high_quality=False):
        """high_quality=False -> UI (rapide), high_quality=True -> export (lent)"""
        source = self.original_image if high_quality else self.low_res_image
        img = source.copy()

        if self.brightness != 1.0: img = ImageEnhance.Brightness(img).enhance(self.brightness)
        if self.contrast != 1.0: img = ImageEnhance.Contrast(img).enhance(self.contrast)
        if self.saturation != 1.0: img = ImageEnhance.Color(img).enhance(self.saturation)
        if self.blur > 0:
            radius = self.blur
            if not high_quality:
                # Ajuster le flou pour la petite image
                radius = self.blur * (source.width / self.original_size[0])
            img = img.filter(ImageFilter.GaussianBlur(radius=radius))

        if high_quality:
            return img
        self.display_image = img
        self._preview_cache.clear()

    def current_aspect(self):
        """Ratio largeur/hauteur de l'image entière après rotation."""
        return (1.0 / self._aspect) if (self.angle % 180) == 90 else self._aspect

    def visible_aspect(self):
        """Ratio de la zone réellement affichée (après rotation et rognage)."""
        cl, ct, cr, cb = self.crop_box_norm
        return self.current_aspect() * max(1e-6, cr - cl) / max(1e-6, cb - ct)

    def rotate_cw(self):
        self.angle = (self.angle - 90) % 360
        self._preview_cache.clear()

    def _rendered_proxy(self):
        """Proxy pivoté puis rogné, mis en cache tant que rien ne change."""
        key = ("base", self.angle, self.crop_box_norm, id(self.display_image))
        cached = self._preview_cache.get(key)
        if cached is not None:
            return cached
        im_rot = self.display_image.rotate(self.angle, expand=True, resample=Image.Resampling.NEAREST)
        rw, rh = im_rot.size
        cl, ct, cr, cb = self.crop_box_norm
        l, t = int(cl * rw), int(ct * rh)
        r, b = int(cr * rw), int(cb * rh)
        if r - l < 1: r = l + 1
        if b - t < 1: b = t + 1
        base = im_rot.crop((l, t, r, b))
        self._preview_cache[key] = base
        return base

    def get_tk_image(self, container_w, container_h):
        # Utilise display_image (low_res) -> rapide
        if container_w <= 0 or container_h <= 0: return None
        cache_key = (container_w, container_h, self.angle, self.crop_box_norm, id(self.display_image))
        if cache_key in self._preview_cache: return self._preview_cache[cache_key]

        im_final = self._rendered_proxy().resize((int(container_w), int(container_h)), Image.Resampling.BILINEAR)

        from PIL import ImageTk
        tk_img = ImageTk.PhotoImage(im_final)
        self._preview_cache[cache_key] = tk_img
        return tk_img

    def get_slice_image(self, l, t, r, b, target_w, target_h):
        """Morceau (l, t, r, b) en coordonnées logiques, rendu à target_w x target_h depuis le proxy."""
        if target_w <= 0 or target_h <= 0 or not self.w or not self.h: return None
        base = self._rendered_proxy()
        bw, bh = base.size
        fx, fy = bw / self.w, bh / self.h
        box = (int(l * fx), int(t * fy), max(int(l * fx) + 1, int(math.ceil(r * fx))), max(int(t * fy) + 1, int(math.ceil(b * fy))))
        return base.crop(box).resize((int(target_w), int(target_h)), Image.Resampling.BILINEAR)

    def get_tk_image_slice(self, l, t, r, b, target_w, target_h):
        """Returns a PhotoImage of a specific slice of this image."""
        try:
            slice_img = self.get_slice_image(l, t, r, b, target_w, target_h)
            if slice_img is None: return None
            from PIL import ImageTk
            return ImageTk.PhotoImage(slice_img)
        except Exception:
            return None


def load_images_from_paths(paths, errors=None):
    """Charge les images ; les échecs sont ajoutés à `errors` (liste de (chemin, message))."""
    res = []
    for p in paths:
        try:
            res.append(LoadedImage(p, open_image_upright(p)))
        except Exception as e:
            if errors is not None:
                errors.append((p, str(e)))
    return res

# --- AUTO LAYOUT ---

class AutoLayoutStrategy:
    # Poids de l'équilibre des tailles dans le score du mode optimal :
    # 0 = seul le remplissage compte (images minuscules possibles), plus haut = tailles plus homogènes.
    OPTIMAL_BALANCE_WEIGHT = 0.15
    OPTIMAL_MAX_TIME = 0.85

    @staticmethod
    def apply(mode, target_w, target_h, images):
        if not images: return

        # Reset des paramètres de base
        for idx, img in enumerate(images):
            img.angle = 0
            img.z_index = idx
            img.crop_box_norm = (0.0, 0.0, 1.0, 1.0) # Reset crop

        if mode == "layout_mosaic": AutoLayoutStrategy._perfect_mosaic(target_w, target_h, images)
        elif mode == "layout_grid": AutoLayoutStrategy._grid_fit(target_w, target_h, images)
        elif mode == "layout_lines": AutoLayoutStrategy._justified_fit(target_w, target_h, images)
        elif mode == "layout_v_strip": AutoLayoutStrategy._vertical_strip(target_w, target_h, images)
        elif mode == "layout_h_strip": AutoLayoutStrategy._horizontal_strip(target_w, target_h, images)
        elif mode == "layout_optimal": AutoLayoutStrategy._optimal_fit(target_w, target_h, images)
        else: AutoLayoutStrategy._perfect_mosaic(target_w, target_h, images) # fallback

    @staticmethod
    def _optimal_fit(tw, th, images, max_time=None):
        """
        Recherche aléatoire d'un arbre de découpage (« slicing floorplan ») : chaque feuille
        a exactement le ratio de son image, donc aucun vide entre les images. Le score
        combine le remplissage de l'écran et l'équilibre des tailles, pour éviter qu'une
        image devienne minuscule. Heuristique bornée dans le temps, sans garantie d'optimum.
        """
        n = len(images)
        if n == 0: return
        elif n == 1:
            AutoLayoutStrategy._apply_fit_inside(images[0], 0, 0, tw, th)
            return

        target_ratio = tw / th
        weight = AutoLayoutStrategy.OPTIMAL_BALANCE_WEIGHT
        max_time = AutoLayoutStrategy.OPTIMAL_MAX_TIME if max_time is None else max_time

        def make_random_tree(imgs_slice):
            # Chaque nœud porte R (ratio) et les aires de ses feuilles pour une hauteur de 1.
            if len(imgs_slice) == 1:
                r = imgs_slice[0].visible_aspect()
                return {"type": "leaf", "img": imgs_slice[0], "R": r, "areas": [r]}

            split_idx = random.randint(1, len(imgs_slice) - 1)
            left = make_random_tree(imgs_slice[:split_idx])
            right = make_random_tree(imgs_slice[split_idx:])

            if random.random() < 0.5:
                R = left["R"] + right["R"]
                areas = left["areas"] + right["areas"]
                return {"type": "H", "left": left, "right": right, "R": R, "areas": areas}

            R = 1.0 / (1.0 / left["R"] + 1.0 / right["R"])
            kl, kr = (R / left["R"]) ** 2, (R / right["R"]) ** 2
            areas = [a * kl for a in left["areas"]] + [a * kr for a in right["areas"]]
            return {"type": "V", "left": left, "right": right, "R": R, "areas": areas}

        def score(tree):
            tr = tree["R"]
            fill = target_ratio / tr if tr >= target_ratio else tr / target_ratio
            areas = tree["areas"]
            balance = min(areas) / max(areas)
            return fill * (balance ** weight)

        best_tree = None
        best_score = -1.0
        start_time = time.perf_counter()
        imgs_copy = images.copy()
        iterations = 0
        while iterations == 0 or time.perf_counter() - start_time < max_time:
            iterations += 1
            if n <= 10 and iterations > 100000:
                break
            random.shuffle(imgs_copy)
            tree = make_random_tree(imgs_copy)
            s = score(tree)
            if s > best_score:
                best_score = s
                best_tree = tree

        R_total = best_tree["R"]
        if R_total >= target_ratio:
            global_w = tw
            global_h = tw / R_total
        else:
            global_h = th
            global_w = th * R_total

        start_x = (tw - global_w) / 2
        start_y = (th - global_h) / 2

        def place_tree(node, x, y, w, h):
            if node["type"] == "leaf":
                AutoLayoutStrategy._apply_fit_inside(node["img"], x, y, w, h)
                return

            left = node["left"]
            right = node["right"]
            if node["type"] == 'H':
                w_left = w * (left["R"] / node["R"])
                w_right = w - w_left
                place_tree(left, x, y, w_left, h)
                place_tree(right, x + w_left, y, w_right, h)
            else:
                inv_l = 1.0 / left["R"]
                inv_r = 1.0 / right["R"]
                h_left = h * (inv_l / (inv_l + inv_r))
                h_right = h - h_left
                place_tree(left, x, y, w, h_left)
                place_tree(right, x, y + h_left, w, h_right)

        place_tree(best_tree, start_x, start_y, global_w, global_h)

    @staticmethod
    def _apply_fit_inside(img, box_x, box_y, box_w, box_h):
        """Place la zone visible de l'image dans la boîte, sans déformation (bandes noires si besoin)."""
        if box_w <= 0 or box_h <= 0: return
        img_ratio = img.visible_aspect(); box_ratio = box_w / box_h

        # Logique Fit Inside
        if img_ratio > box_ratio: # Image plus large que la boîte
            new_w = box_w
            new_h = box_w / img_ratio
        else: # Image plus haute
            new_h = box_h
            new_w = box_h * img_ratio

        offset_x = (box_w - new_w) / 2
        offset_y = (box_h - new_h) / 2
        img.x = box_x + offset_x; img.y = box_y + offset_y
        img.w = int(new_w); img.h = int(new_h)

    @staticmethod
    def _apply_crop_cover(img, target_w, target_h):
        """Helper pour centrer et rogner l'image dans sa case sans la déformer."""
        if target_w <= 0 or target_h <= 0: return

        # Affectation géométrie
        img.w = int(target_w)
        img.h = int(target_h)

        # Calcul du crop
        box_ratio = target_w / target_h
        img_ratio = img.current_aspect()

        if img_ratio > box_ratio:
            # Image trop large : on coupe gauche/droite
            visible_fraction = box_ratio / img_ratio
            margin = (1.0 - visible_fraction) / 2
            img.crop_box_norm = (margin, 0.0, 1.0 - margin, 1.0)
        else:
            # Image trop haute : on coupe haut/bas
            visible_fraction = img_ratio / box_ratio
            margin = (1.0 - visible_fraction) / 2
            img.crop_box_norm = (0.0, margin, 1.0, 1.0 - margin)

    @staticmethod
    def _justified_fit(tw, th, images):
        """
        Crée des lignes pour remplir TW. Et réduit le tout si nécessaire pour rentrer dans TH (Fit Inside).
        """
        if not images: return
        ratios = [img.visible_aspect() for img in images]
        total_ratio = sum(ratios)
        screen_ratio = tw / th

        ideal_rows = max(1, round(total_ratio / screen_ratio))
        rows = []
        current_row = []
        current_row_ratio = 0.0
        avg_target_row_ratio = total_ratio / ideal_rows

        for i, img in enumerate(images):
            current_row.append(img)
            current_row_ratio += ratios[i]
            if current_row_ratio >= avg_target_row_ratio and len(rows) < ideal_rows - 1:
                rows.append((current_row, current_row_ratio))
                current_row = []
                current_row_ratio = 0.0
        if current_row:
            rows.append((current_row, current_row_ratio))

        row_heights = []
        total_used_height = 0
        for r_imgs, r_ratio in rows:
            if r_ratio == 0: continue
            h = tw / r_ratio
            row_heights.append(h)
            total_used_height += h

        scale_factor = min(1.0, th / total_used_height) if total_used_height > 0 else 1.0
        current_y = (th - (total_used_height * scale_factor)) / 2

        for idx_row, (r_imgs, r_ratio) in enumerate(rows):
            h_raw = row_heights[idx_row]
            final_h = h_raw * scale_factor
            current_x = (tw - (tw * scale_factor)) / 2
            for img in r_imgs:
                w = final_h * img.visible_aspect()
                AutoLayoutStrategy._apply_fit_inside(img, current_x, current_y, w, final_h)
                current_x += w
            current_y += final_h

    @staticmethod
    def _perfect_mosaic(tw, th, images):
        """
        Patchwork aléatoire (découpage binaire de l'espace). Chaque image est placée en
        Fit Inside dans sa cellule : rien n'est rogné, mais des bandes noires restent
        possibles entre les images. Pour réduire le vide, utiliser le mode optimal.
        """
        if not images: return

        # On mélange légèrement pour l'effet patchwork
        shuffled = images.copy()
        random.shuffle(shuffled)

        AutoLayoutStrategy._recursive_perfect_bsp(0, 0, tw, th, shuffled)

    @staticmethod
    def _recursive_perfect_bsp(x, y, w, h, images):
        n = len(images)
        if n == 0: return

        # Cas de base: 1 seule image pour cette zone
        if n == 1:
            img = images[0]
            AutoLayoutStrategy._apply_fit_inside(img, x, y, w, h)
            return

        # On coupe aléatoirement le côté le plus long souvent, mais parfois le court
        # pour un effet patchwork plus dynamique.
        if w > h * 1.5:
            split_vertical = True
        elif h > w * 1.5:
            split_vertical = False
        else:
            split_vertical = random.choice([True, False])

        # On coupe la liste des images aléatoirement pour éviter des grilles parfaites
        if n == 2:
            split_idx = 1
        else:
            # coupe aléatoire entre 1 et n-1
            split_idx = random.randint(1, n - 1)

        group_a = images[:split_idx]
        group_b = images[split_idx:]

        # La taille physique de la découpe dépend du ratio du nombre d'images,
        # avec une petite marge d'aléatoire pour le style patchwork.
        base_ratio = len(group_a) / n
        jitter = random.uniform(-0.1, 0.1) # +/- 10%
        final_ratio = max(0.2, min(0.8, base_ratio + jitter))

        if split_vertical:
            w_a = w * final_ratio
            w_b = w - w_a
            AutoLayoutStrategy._recursive_perfect_bsp(x, y, w_a, h, group_a)
            AutoLayoutStrategy._recursive_perfect_bsp(x + w_a, y, w_b, h, group_b)
        else:
            h_a = h * final_ratio
            h_b = h - h_a
            AutoLayoutStrategy._recursive_perfect_bsp(x, y, w, h_a, group_a)
            AutoLayoutStrategy._recursive_perfect_bsp(x, y + h_a, w, h_b, group_b)

    @staticmethod
    def _grid_fit(tw, th, images):
        if not images: return
        count = len(images)
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        cw, ch = tw / cols, th / rows
        for i, img in enumerate(images):
            col_idx = i % cols
            row_idx = i // cols

            # Gestion de la dernière ligne incomplète
            items_in_this_row = count - (row_idx * cols)
            if row_idx == rows - 1 and items_in_this_row < cols:
                special_w = tw / items_in_this_row
                AutoLayoutStrategy._apply_fit_inside(img, col_idx * special_w, row_idx * ch, special_w, ch)
            else:
                AutoLayoutStrategy._apply_fit_inside(img, col_idx * cw, row_idx * ch, cw, ch)

    @staticmethod
    def _horizontal_strip(tw, th, images):
        count = len(images)
        if count == 0: return
        ch = th / count
        for i, img in enumerate(images):
            AutoLayoutStrategy._apply_fit_inside(img, 0, i * ch, tw, ch)

    @staticmethod
    def _vertical_strip(tw, th, images):
        count = len(images)
        if count == 0: return
        cw = tw / count
        for i, img in enumerate(images):
            AutoLayoutStrategy._apply_fit_inside(img, i * cw, 0, cw, th)

# --- PROJETS (JSON) ---

def image_to_project_entry(img):
    return {
        "path": img.path,
        "x": img.x, "y": img.y, "w": img.w, "h": img.h,
        "angle": img.angle, "z": img.z_index,
        "crop": list(img.crop_box_norm),
        "brightness": img.brightness, "contrast": img.contrast,
        "saturation": img.saturation, "blur": img.blur,
    }


def save_project_json(path, data):
    """Enregistre un projet. Les chemins d'images sont stockés relativement au fichier projet."""
    data = copy.deepcopy(data)
    data["version"] = PROJECT_SCHEMA_VERSION
    base = os.path.dirname(os.path.abspath(path))
    for img in data.get("images", []):
        try:
            img["path"] = os.path.relpath(img["path"], base)
        except ValueError:
            # Autre lecteur Windows : on garde le chemin absolu.
            img["path"] = os.path.abspath(img["path"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _number(entry, key, default, minimum=None, maximum=None):
    value = entry.get(key, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or math.isnan(value):
        raise ValueError(f"valeur invalide pour « {key} »")
    if minimum is not None: value = max(minimum, value)
    if maximum is not None: value = min(maximum, value)
    return value


def load_project_json(path, errors=None):
    """
    Charge un projet. Retourne (meta, images). Chaque image introuvable ou invalide
    est ajoutée à `errors` (liste de (chemin, message)) au lieu d'être ignorée en silence.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    version = data.get("version", PROJECT_SCHEMA_VERSION)
    if not isinstance(version, int) or version > PROJECT_SCHEMA_VERSION:
        raise ValueError(f"Version de projet non prise en charge : {version}")

    base = os.path.dirname(os.path.abspath(path))
    imgs = []
    for s in sorted(data.get("images", []), key=lambda x: x.get("z", 0)):
        raw_path = s.get("path", "")
        full = raw_path if os.path.isabs(raw_path) else os.path.join(base, raw_path)
        try:
            if not os.path.isfile(full):
                raise FileNotFoundError("fichier introuvable")
            li = LoadedImage(full, open_image_upright(full))
            li.x, li.y = _number(s, "x", 0), _number(s, "y", 0)
            li.w = int(_number(s, "w", 100, minimum=1)); li.h = int(_number(s, "h", 100, minimum=1))
            angle = int(_number(s, "angle", 0)) % 360
            li.angle = angle - (angle % 90)
            li.z_index = int(_number(s, "z", 0))
            crop = s.get("crop", [0, 0, 1, 1])
            if not (isinstance(crop, (list, tuple)) and len(crop) == 4):
                raise ValueError("zone de rognage invalide")
            cl, ct, cr, cb = [min(1.0, max(0.0, float(v))) for v in crop]
            if cr - cl < 0.01 or cb - ct < 0.01:
                raise ValueError("zone de rognage invalide")
            li.crop_box_norm = (cl, ct, cr, cb)
            li.brightness = _number(s, "brightness", 1.0, 0.0, 4.0)
            li.contrast = _number(s, "contrast", 1.0, 0.0, 4.0)
            li.saturation = _number(s, "saturation", 1.0, 0.0, 4.0)
            li.blur = _number(s, "blur", 0.0, 0.0, 100.0)
            li.apply_filters(high_quality=False)
            imgs.append(li)
        except Exception as e:
            if errors is not None:
                errors.append((raw_path, str(e)))
    return data.get("meta", {}), imgs


def compose_wallpaper_contain(ts, images, bg):
    """Rendu HD de la composition complète à partir des fichiers originaux."""
    canvas = Image.new("RGB", ts, bg)
    for li in sorted(images, key=lambda i: i.z_index):
        src = li.apply_filters(high_quality=True)
        src = src.rotate(li.angle, expand=True, resample=Image.Resampling.BICUBIC)
        sw, sh = src.size
        cl, ct, cr, cb = li.crop_box_norm
        src = src.crop((int(cl*sw), int(ct*sh), int(cr*sw), int(cb*sh)))
        # Bords arrondis séparément : deux images voisines se touchent sans liseré d'1 px.
        x0, y0 = int(round(li.x)), int(round(li.y))
        if li.w and li.h:
            x1, y1 = int(round(li.x + li.w)), int(round(li.y + li.h))
            src = src.resize((max(1, x1 - x0), max(1, y1 - y0)), Image.Resampling.LANCZOS)
        canvas.paste(src, (x0, y0), src if src.mode == 'RGBA' else None)
    return canvas
