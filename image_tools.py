# image_tools.py
import copy
import hashlib
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
        "_preview_cache", "_aspect", "z_index", "_focus"
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
        self._focus = None  # point d'intérêt (x, y) normalisé, calculé à la demande
        iw, ih = self.original_size
        self._aspect = (iw / ih) if ih else 1.0

    def _can_reload(self):
        return isinstance(self.path, str) and os.path.isfile(self.path)

    @property
    def focus(self):
        """Point d'intérêt normalisé (x, y) : visages détectés, sinon zone la plus détaillée."""
        if self._focus is None:
            from facefocus import find_focus
            self._focus = find_focus(self.low_res_image)
        return self._focus

    @focus.setter
    def focus(self, value):
        self._focus = value

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
        new_obj._focus = self._focus
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
    """
    Dispositions automatiques. Toutes sont déterministes : mêmes images, même écran et même
    numéro de variante donnent toujours le même résultat.

    fill=False (« Ajuster ») : chaque image entière, sans rognage ni déformation ; des bandes
    noires peuvent rester. fill=True (« Remplir ») : chaque case est remplie, l'image est
    recadrée autour de son point d'intérêt (visages détectés, sinon zone la plus détaillée).
    """
    # Poids de l'équilibre des tailles dans le score du mode optimal :
    # 0 = seul le remplissage compte (images minuscules possibles), plus haut = tailles plus homogènes.
    OPTIMAL_BALANCE_WEIGHT = 0.15
    OPTIMAL_MAX_TIME = 2.0  # garde-fou ; normalement le nombre d'essais s'arrête avant
    VARIANT_COUNT = 4

    @staticmethod
    def _seed(mode, tw, th, images, variant):
        key = repr((mode, round(tw), round(th), variant,
                    [(str(i.path), round(i.visible_aspect(), 4)) for i in images]))
        return int(hashlib.sha1(key.encode()).hexdigest()[:12], 16)

    @staticmethod
    def apply(mode, target_w, target_h, images, fill=False, variant=0):
        if not images: return

        # Reset des paramètres de base
        for idx, img in enumerate(images):
            img.angle = 0
            img.z_index = idx
            img.crop_box_norm = (0.0, 0.0, 1.0, 1.0) # Reset crop

        rng = random.Random(AutoLayoutStrategy._seed(mode, target_w, target_h, images, variant))
        place = AutoLayoutStrategy._apply_crop_cover if fill else AutoLayoutStrategy._apply_fit_inside
        ordered = AutoLayoutStrategy._ordered(images, variant) if mode in ("layout_grid", "layout_lines", "layout_v_strip", "layout_h_strip") else images

        if mode == "layout_grid": AutoLayoutStrategy._grid_fit(target_w, target_h, ordered, place)
        elif mode == "layout_lines": AutoLayoutStrategy._justified_fit(target_w, target_h, ordered, place, fill)
        elif mode == "layout_v_strip": AutoLayoutStrategy._vertical_strip(target_w, target_h, ordered, place)
        elif mode == "layout_h_strip": AutoLayoutStrategy._horizontal_strip(target_w, target_h, ordered, place)
        elif mode == "layout_optimal": AutoLayoutStrategy._optimal_fit(target_w, target_h, images, rng=rng, variant=variant, fill=fill)
        else: AutoLayoutStrategy._perfect_mosaic(target_w, target_h, images, rng, place)

    @staticmethod
    def _ordered(images, variant):
        """Ordres déterministes pour les dispositions régulières : variante 0 = ordre d'import."""
        v = variant % 4
        if v == 0: return list(images)
        if v == 1: return list(reversed(images))
        if v == 2: return sorted(images, key=lambda i: -i.visible_aspect())
        return sorted(images, key=lambda i: i.visible_aspect())

    @staticmethod
    def place_on_screens(images, rects, fill=False):
        """Une image par écran (rects = rectangles de composition des écrans)."""
        place = AutoLayoutStrategy._apply_crop_cover if fill else AutoLayoutStrategy._apply_fit_inside
        for idx, (img, (x, y, w, h)) in enumerate(zip(images, rects)):
            img.angle = 0
            img.z_index = idx
            img.crop_box_norm = (0.0, 0.0, 1.0, 1.0)
            place(img, x, y, w, h)

    @staticmethod
    def variants(mode, tw, th, images, fill=False, count=None):
        """
        Calcule `count` variantes distinctes sans toucher aux images.
        Retourne une liste de placements : [(x, y, w, h, crop, z) par image].
        """
        count = count or AutoLayoutStrategy.VARIANT_COUNT
        results, seen = [], set()
        for variant in range(count * 3):
            clones = [i.clone() for i in images]
            AutoLayoutStrategy.apply(mode, tw, th, clones, fill=fill, variant=variant)
            placement = [(c.x, c.y, c.w, c.h, c.crop_box_norm, c.z_index) for c in clones]
            key = tuple((round(p[0] / 4), round(p[1] / 4), round(p[2] / 4), round(p[3] / 4)) for p in placement)
            if key in seen:
                continue
            seen.add(key)
            results.append(placement)
            if len(results) == count:
                break
        return results

    @staticmethod
    def apply_placement(images, placement):
        for img, (x, y, w, h, crop, z) in zip(images, placement):
            img.angle = 0
            img.x, img.y, img.w, img.h = x, y, w, h
            img.crop_box_norm = crop
            img.z_index = z

    @staticmethod
    def _optimal_fit(tw, th, images, rng=None, variant=0, fill=False, iterations=None, max_time=None):
        """
        Recherche d'un arbre de découpage (« slicing floorplan ») : chaque feuille a exactement
        le ratio de son image, donc aucun vide entre les images. Le score combine le remplissage
        de l'écran et l'équilibre des tailles, pour éviter qu'une image devienne minuscule.
        Nombre d'essais fixe et graine fixe : le résultat est reproductible. `variant` = k-ième
        meilleur arbre distinct. En mode Remplir, l'arbre est étiré à tout l'écran et chaque
        image est recadrée dans sa case.
        """
        n = len(images)
        if n == 0: return
        place = AutoLayoutStrategy._apply_crop_cover if fill else AutoLayoutStrategy._apply_fit_inside
        if n == 1:
            place(images[0], 0, 0, tw, th)
            return

        rng = rng or random.Random(0)
        target_ratio = tw / th
        weight = AutoLayoutStrategy.OPTIMAL_BALANCE_WEIGHT
        max_time = AutoLayoutStrategy.OPTIMAL_MAX_TIME if max_time is None else max_time
        iterations = iterations or (60000 if n <= 6 else 30000 if n <= 12 else 15000)
        keep = variant + 1

        def make_random_tree(imgs_slice):
            # Chaque nœud porte R (ratio) et les aires de ses feuilles pour une hauteur de 1.
            if len(imgs_slice) == 1:
                r = imgs_slice[0].visible_aspect()
                return {"type": "leaf", "img": imgs_slice[0], "R": r, "areas": [r], "key": id(imgs_slice[0])}

            split_idx = rng.randint(1, len(imgs_slice) - 1)
            left = make_random_tree(imgs_slice[:split_idx])
            right = make_random_tree(imgs_slice[split_idx:])

            if rng.random() < 0.5:
                R = left["R"] + right["R"]
                areas = left["areas"] + right["areas"]
                return {"type": "H", "left": left, "right": right, "R": R, "areas": areas, "key": ("H", left["key"], right["key"])}

            R = 1.0 / (1.0 / left["R"] + 1.0 / right["R"])
            kl, kr = (R / left["R"]) ** 2, (R / right["R"]) ** 2
            areas = [a * kl for a in left["areas"]] + [a * kr for a in right["areas"]]
            return {"type": "V", "left": left, "right": right, "R": R, "areas": areas, "key": ("V", left["key"], right["key"])}

        def score(tree):
            tr = tree["R"]
            fill_ratio = target_ratio / tr if tr >= target_ratio else tr / target_ratio
            areas = tree["areas"]
            return fill_ratio * ((min(areas) / max(areas)) ** weight)

        best = []  # [(score, ordre, arbre)] trié, clés distinctes
        keys = set()
        start_time = time.perf_counter()
        imgs_copy = list(images)
        for it in range(iterations):
            if it % 2000 == 0 and it and time.perf_counter() - start_time > max_time:
                break
            rng.shuffle(imgs_copy)
            tree = make_random_tree(imgs_copy)
            if tree["key"] in keys:
                continue
            s = score(tree)
            if len(best) < keep or s > best[-1][0]:
                keys.add(tree["key"])
                best.append((s, it, tree))
                best.sort(key=lambda t: (-t[0], t[1]))
                if len(best) > keep:
                    keys.discard(best.pop()[2]["key"])
        best_tree = best[min(variant, len(best) - 1)][2]

        R_total = best_tree["R"]
        if fill:
            global_w, global_h = tw, th
        elif R_total >= target_ratio:
            global_w = tw
            global_h = tw / R_total
        else:
            global_h = th
            global_w = th * R_total

        start_x = (tw - global_w) / 2
        start_y = (th - global_h) / 2

        def place_tree(node, x, y, w, h):
            if node["type"] == "leaf":
                place(node["img"], x, y, w, h)
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
    def _apply_crop_cover(img, box_x, box_y, box_w, box_h):
        """
        Remplit toute la boîte sans déformation : l'image est recadrée au ratio de la boîte,
        la fenêtre étant centrée sur le point d'intérêt (img.focus) et maintenue dans l'image.
        """
        if box_w <= 0 or box_h <= 0: return
        img.x, img.y = box_x, box_y
        img.w, img.h = max(1, int(round(box_w))), max(1, int(round(box_h)))
        box_ratio = box_w / box_h
        img_ratio = img.current_aspect()
        fx, fy = img.focus if img.focus else (0.5, 0.5)
        if img_ratio > box_ratio:
            # Image trop large : on garde une bande verticale
            frac = box_ratio / img_ratio
            left = min(max(fx - frac / 2, 0.0), 1.0 - frac)
            img.crop_box_norm = (left, 0.0, left + frac, 1.0)
        else:
            # Image trop haute : on garde une bande horizontale
            frac = img_ratio / box_ratio
            top = min(max(fy - frac / 2, 0.0), 1.0 - frac)
            img.crop_box_norm = (0.0, top, 1.0, top + frac)

    @staticmethod
    def _justified_fit(tw, th, images, place=None, fill=False):
        """
        Crée des lignes pour remplir TW. Et réduit le tout si nécessaire pour rentrer dans TH (Fit Inside).
        En mode Remplir, les lignes sont étirées à toute la hauteur et les images recadrées.
        """
        if not images: return
        place = place or AutoLayoutStrategy._apply_fit_inside
        ratios = [img.visible_aspect() for img in images]
        total_ratio = sum(ratios)
        screen_ratio = tw / th

        ideal_rows = max(1, min(len(images), round(total_ratio / screen_ratio)))
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

        row_heights = [tw / r_ratio for _, r_ratio in rows if r_ratio > 0]
        total_used_height = sum(row_heights)

        if fill:
            y_scale = th / total_used_height if total_used_height > 0 else 1.0
            current_y = 0.0
            for (r_imgs, r_ratio), h_raw in zip(rows, row_heights):
                row_h = h_raw * y_scale
                current_x = 0.0
                for img in r_imgs:
                    w = tw * img.visible_aspect() / r_ratio
                    place(img, current_x, current_y, w, row_h)
                    current_x += w
                current_y += row_h
            return

        scale_factor = min(1.0, th / total_used_height) if total_used_height > 0 else 1.0
        current_y = (th - (total_used_height * scale_factor)) / 2

        for (r_imgs, r_ratio), h_raw in zip(rows, row_heights):
            final_h = h_raw * scale_factor
            current_x = (tw - (tw * scale_factor)) / 2
            for img in r_imgs:
                w = final_h * img.visible_aspect()
                place(img, current_x, current_y, w, final_h)
                current_x += w
            current_y += final_h

    @staticmethod
    def _perfect_mosaic(tw, th, images, rng=None, place=None):
        """
        Patchwork (découpage binaire de l'espace). En mode Ajuster, chaque image est placée
        entière dans sa cellule (bandes noires possibles) ; en mode Remplir, elle la couvre.
        """
        if not images: return
        rng = rng or random.Random(0)
        place = place or AutoLayoutStrategy._apply_fit_inside

        # On mélange légèrement pour l'effet patchwork
        shuffled = list(images)
        rng.shuffle(shuffled)

        AutoLayoutStrategy._recursive_perfect_bsp(0, 0, tw, th, shuffled, rng, place)

    @staticmethod
    def _recursive_perfect_bsp(x, y, w, h, images, rng, place):
        n = len(images)
        if n == 0: return

        # Cas de base: 1 seule image pour cette zone
        if n == 1:
            place(images[0], x, y, w, h)
            return

        # On coupe le côté le plus long, parfois le court pour un effet patchwork.
        if w > h * 1.5:
            split_vertical = True
        elif h > w * 1.5:
            split_vertical = False
        else:
            split_vertical = rng.choice([True, False])

        split_idx = 1 if n == 2 else rng.randint(1, n - 1)

        group_a = images[:split_idx]
        group_b = images[split_idx:]

        # La taille de la découpe suit la proportion d'images, avec un peu d'aléatoire reproductible.
        base_ratio = len(group_a) / n
        jitter = rng.uniform(-0.1, 0.1) # +/- 10%
        final_ratio = max(0.2, min(0.8, base_ratio + jitter))

        if split_vertical:
            w_a = w * final_ratio
            AutoLayoutStrategy._recursive_perfect_bsp(x, y, w_a, h, group_a, rng, place)
            AutoLayoutStrategy._recursive_perfect_bsp(x + w_a, y, w - w_a, h, group_b, rng, place)
        else:
            h_a = h * final_ratio
            AutoLayoutStrategy._recursive_perfect_bsp(x, y, w, h_a, group_a, rng, place)
            AutoLayoutStrategy._recursive_perfect_bsp(x, y + h_a, w, h - h_a, group_b, rng, place)

    @staticmethod
    def _grid_fit(tw, th, images, place=None):
        if not images: return
        place = place or AutoLayoutStrategy._apply_fit_inside
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
                place(img, col_idx * special_w, row_idx * ch, special_w, ch)
            else:
                place(img, col_idx * cw, row_idx * ch, cw, ch)

    @staticmethod
    def _horizontal_strip(tw, th, images, place=None):
        count = len(images)
        if count == 0: return
        place = place or AutoLayoutStrategy._apply_fit_inside
        ch = th / count
        for i, img in enumerate(images):
            place(img, 0, i * ch, tw, ch)

    @staticmethod
    def _vertical_strip(tw, th, images, place=None):
        count = len(images)
        if count == 0: return
        place = place or AutoLayoutStrategy._apply_fit_inside
        cw = tw / count
        for i, img in enumerate(images):
            place(img, i * cw, 0, cw, th)

# --- PROJETS (JSON) ---

def image_to_project_entry(img):
    return {
        "path": img.path,
        "x": img.x, "y": img.y, "w": img.w, "h": img.h,
        "angle": img.angle, "z": img.z_index,
        "crop": list(img.crop_box_norm),
        "brightness": img.brightness, "contrast": img.contrast,
        "saturation": img.saturation, "blur": img.blur,
        "focus": list(img._focus) if img._focus else None,
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
            focus = s.get("focus")
            if isinstance(focus, (list, tuple)) and len(focus) == 2:
                li._focus = (min(1.0, max(0.0, float(focus[0]))), min(1.0, max(0.0, float(focus[1]))))
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
