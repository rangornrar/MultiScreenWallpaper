# image_tools.py
from PIL import Image, ImageEnhance, ImageFilter
import math
import json
import os
import random

class LoadedImage:
    """
    Optimisation Performance :
    - low_res_image (Proxy) : Utilisé pour l'affichage temps réel dans Tkinter.
    - original_image : Utilisé uniquement pour l'export final haute qualité.
    """
    __slots__ = (
        "path", "original_image", "low_res_image", "display_image", 
        "x", "y", "w", "h", 
        "angle", "crop_box_norm", 
        "brightness", "contrast", "saturation", "blur",
        "_preview_cache", "_aspect", "z_index"
    )

    def __init__(self, path, image: Image.Image):
        self.path = path
        self.original_image = image.convert("RGBA")
        
        # Création du PROXY (Max 1024px)
        self.low_res_image = self.original_image.copy()
        self.low_res_image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        self.display_image = self.low_res_image
        
        self.x = 0; self.y = 0; self.w = None; self.h = None
        self.angle = 0; self.z_index = 0
        self.crop_box_norm = (0.0, 0.0, 1.0, 1.0) 

        self.brightness = 1.0; self.contrast = 1.0
        self.saturation = 1.0; self.blur = 0.0

        self._preview_cache = {}
        iw, ih = self.original_image.size
        self._aspect = (iw / ih) if ih else 1.0

    def clone(self):
        # Clone optimisé (références partagées pour images lourdes)
        new_obj = LoadedImage.__new__(LoadedImage)
        new_obj.path = self.path
        new_obj.original_image = self.original_image
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
        """high_quality=False -> UI (Rapide), high_quality=True -> Export (Lent)"""
        source = self.original_image if high_quality else self.low_res_image
        img = source.copy()
        
        if self.brightness != 1.0: img = ImageEnhance.Brightness(img).enhance(self.brightness)
        if self.contrast != 1.0: img = ImageEnhance.Contrast(img).enhance(self.contrast)
        if self.saturation != 1.0: img = ImageEnhance.Color(img).enhance(self.saturation)
        if self.blur > 0:
            radius = self.blur
            if not high_quality:
                # Ajuster le flou pour la petite image
                radius = self.blur * (source.width / self.original_image.width)
            img = img.filter(ImageFilter.GaussianBlur(radius=radius))
            
        if high_quality: return img
        else:
            self.display_image = img
            self._preview_cache.clear()

    def current_aspect(self):
        return (1.0 / self._aspect) if (self.angle % 180) == 90 else self._aspect

    def rotate_cw(self):
        self.angle = (self.angle - 90) % 360
        self._preview_cache.clear()

    def get_tk_image(self, container_w, container_h):
        # Utilise display_image (low_res) -> Ultra rapide
        if container_w <= 0 or container_h <= 0: return None
        cache_key = (container_w, container_h, self.angle, self.crop_box_norm, id(self.display_image))
        if cache_key in self._preview_cache: return self._preview_cache[cache_key]

        im_rot = self.display_image.rotate(self.angle, expand=True, resample=Image.Resampling.NEAREST)
        rw, rh = im_rot.size
        cl, ct, cr, cb = self.crop_box_norm
        l, t = int(cl * rw), int(ct * rh)
        r, b = int(cr * rw), int(cb * rh)
        if r - l < 1: r = l + 1
        if b - t < 1: b = t + 1
        
        im_cropped = im_rot.crop((l, t, r, b))
        im_final = im_cropped.resize((int(container_w), int(container_h)), Image.Resampling.BILINEAR)

        from PIL import ImageTk
        tk_img = ImageTk.PhotoImage(im_final)
        self._preview_cache[cache_key] = tk_img
        return tk_img

def load_images_from_paths(paths):
    res = []
    for p in paths:
        try:
            im = Image.open(p); im.load()
            res.append(LoadedImage(p, im))
        except Exception as e: print(f"Err {p}: {e}")
    return res

# --- AUTO LAYOUT ---
# image_tools.py (Partie AutoLayoutStrategy mise à jour)

# image_tools.py (Partie AutoLayoutStrategy)

class AutoLayoutStrategy:
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
    def _optimal_fit(tw, th, images):
        """
        Trouve la meilleure combinaison avec un Slicing Floorplan qui 
        maximise l'aire globale à l'écran sans aucun trou entre les images.
        """
        import time
        import random
        
        n = len(images)
        if n == 0: return
        elif n == 1:
            AutoLayoutStrategy._apply_fit_inside(images[0], 0, 0, tw, th)
            return
            
        target_ratio = tw / th
        
        def make_random_tree(imgs_slice):
            if len(imgs_slice) == 1:
                return {"type": "leaf", "img": imgs_slice[0], "R": imgs_slice[0].current_aspect()}
            
            split_idx = random.randint(1, len(imgs_slice) - 1)
            left = make_random_tree(imgs_slice[:split_idx])
            right = make_random_tree(imgs_slice[split_idx:])
            
            op = random.choice(['H', 'V'])
            if op == 'H':
                R = left["R"] + right["R"]
            else:
                R = 1.0 / (1.0 / left["R"] + 1.0 / right["R"])
                
            return {"type": op, "left": left, "right": right, "R": R}

        best_tree = None
        best_score = -1
        
        start_time = time.time()
        max_time = 0.85
        
        imgs_copy = images.copy()
        
        iterations = 0
        while time.time() - start_time < max_time:
            iterations += 1
            if n <= 10 and iterations > 100000:
                break
                
            random.shuffle(imgs_copy)
            tree = make_random_tree(imgs_copy)
            
            TR = tree["R"]
            if TR >= target_ratio:
                score = target_ratio / TR
            else:
                score = TR / target_ratio
                
            if score > best_score:
                best_score = score
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
        """Place l'image entière dans la boite (avec bandes noires si nécessaire)."""
        if box_w <= 0 or box_h <= 0: return
        img_ratio = img.current_aspect(); box_ratio = box_w / box_h
        
        # Logique Fit Inside
        if img_ratio > box_ratio: # Image plus large que la boite
            new_w = box_w
            new_h = box_w / img_ratio
        else: # Image plus haute
            new_h = box_h
            new_w = box_h * img_ratio
            
        offset_x = (box_w - new_w) / 2
        offset_y = (box_h - new_h) / 2
        img.x = box_x + offset_x; img.y = box_y + offset_y
        img.w = int(new_w); img.h = int(new_h)
        img.crop_box_norm = (0.0, 0.0, 1.0, 1.0) # Pas de crop

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
        ratios = [img.current_aspect() for img in images]
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
                w = final_h * img.current_aspect()
                AutoLayoutStrategy._apply_fit_inside(img, current_x, current_y, w, final_h)
                current_x += w
            current_y += final_h

    @staticmethod
    def _perfect_mosaic(tw, th, images):
        """
        Garantit que 100% de l'espace (tw, th) est couvert, sans aucunes bandes noires.
        1. S'il n'y a qu'1 image, elle remplit tout.
        2. Sinon, on utilise un BSP aléatoire équilibré où chaque cellule résultat
           est remplie avec _apply_crop_cover() au lieu de _apply_fit_inside().
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
            
# IO
def save_project_json(path, data):
    base = os.path.dirname(os.path.abspath(path))
    if "images" in data:
        for img in data["images"]:
            try: img["path"] = os.path.relpath(img["path"], base)
            except: pass
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)

def load_project_json(path):
    with open(path, "r", encoding="utf-8") as f: data = json.load(f)
    base = os.path.dirname(os.path.abspath(path))
    imgs = []
    for s in sorted(data.get("images", []), key=lambda x: x.get("z", 0)):
        full = os.path.join(base, s["path"]) if not os.path.exists(s["path"]) else s["path"]
        if os.path.exists(full):
            try:
                li = LoadedImage(full, Image.open(full))
                li.x, li.y = s.get("x",0), s.get("y",0); li.w, li.h = s.get("w",100), s.get("h",100)
                li.angle, li.z_index = s.get("angle",0), s.get("z",0)
                li.crop_box_norm = tuple(s.get("crop", [0,0,1,1]))
                li.brightness = s.get("brightness", 1.0); li.contrast = s.get("contrast", 1.0)
                li.saturation = s.get("saturation", 1.0); li.blur = s.get("blur", 0.0)
                li.apply_filters(high_quality=False)
                imgs.append(li)
            except: pass
    return data.get("meta", {}), imgs

def compose_wallpaper_contain(ts, images, bg):
    print("Export HD en cours...")
    canvas = Image.new("RGB", ts, bg)
    for li in sorted(images, key=lambda i: i.z_index):
        # On utilise le mode High Quality ici !
        src = li.apply_filters(high_quality=True)
        src = src.rotate(li.angle, expand=True, resample=Image.Resampling.BICUBIC)
        sw, sh = src.size
        cl, ct, cr, cb = li.crop_box_norm
        src = src.crop((int(cl*sw), int(ct*sh), int(cr*sw), int(cb*sh)))
        if li.w and li.h: src = src.resize((li.w, li.h), Image.Resampling.LANCZOS)
        canvas.paste(src, (int(li.x), int(li.y)), src if src.mode=='RGBA' else None)
    return canvas