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

        if mode == "grid": AutoLayoutStrategy._grid_cover(target_w, target_h, images)
        elif mode == "horizontal": AutoLayoutStrategy._horizontal_strip(target_w, target_h, images)
        elif mode == "masonry": AutoLayoutStrategy._masonry(target_w, target_h, images)
        elif mode == "smart_mosaic": AutoLayoutStrategy._mosaic_smart(target_w, target_h, images) # <--- NOUVEAU
        elif mode == "smart_bsp": AutoLayoutStrategy._mosaic_bsp(0, 0, target_w, target_h, images) # <--- NOUVEAU
        elif mode == "justified": AutoLayoutStrategy._justified_optimized(target_w, target_h, images) # <--- NOUVEAU
        elif mode == "lapis": AutoLayoutStrategy._lapis_weighted(target_w, target_h, images) # <--- NOUVEAU

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
    def _lapis_weighted(target_w, target_h, images):
        """
        Mélange les images (aléatoire) mais calcule la taille des cases 
        selon le poids des images (optimisation espace).
        """
        if not images: return
        
        # 1. Aléatoire : On mélange l'ordre des images
        shuffled = images.copy()
        random.shuffle(shuffled)
        
        # 2. Découpe récursive intelligente
        AutoLayoutStrategy._recursive_weighted_split(0, 0, target_w, target_h, shuffled)

    @staticmethod
    def _recursive_weighted_split(x, y, w, h, images):
        n = len(images)
        if n == 0: return
        
        # Cas de base
        if n == 1:
            AutoLayoutStrategy._apply_fit_inside(images[0], x, y, w, h)
            return

        # Décision : On coupe le côté le plus long pour éviter les rectangles trop fins
        split_vertical = w > h

        # Calcul des poids pour minimiser les bandes noires
        # Si on coupe Verticalement, on veut équilibrer la somme des largeurs relatives (Aspect Ratio)
        # Si on coupe Horizontalement, on veut équilibrer la somme des hauteurs relatives (1 / Aspect Ratio)
        if split_vertical:
            ratios = [img.current_aspect() for img in images]
        else:
            ratios = [1.0 / img.current_aspect() for img in images]
        
        total_weight = sum(ratios)
        
        # Découpe de la LISTE des images
        # Pour garder un effet "Lapis" (mosaïque irrégulière), on ne coupe pas forcément au milieu de la liste.
        # On coupe à un index aléatoire, mais on évite les extrêmes (0 ou N)
        if n == 2:
            split_idx = 1
        else:
            # On choisit un point de coupure aléatoire dans la liste (entre 1 et N-1)
            # C'est ça qui crée la variété de tailles (un groupe de 2 vs un groupe de 10)
            split_idx = random.randint(1, n - 1)
        
        group_a = images[:split_idx]
        group_b = images[split_idx:]
        
        # Calcul du poids du groupe A
        weight_a = sum(ratios[:split_idx])
        
        # Pourcentage de l'espace que le groupe A "mérite" pour être bien affiché
        split_pct = weight_a / total_weight if total_weight > 0 else 0.5
        
        # Application de la découpe physique de l'écran
        if split_vertical:
            w_a = w * split_pct
            w_b = w - w_a
            # Récursion
            AutoLayoutStrategy._recursive_weighted_split(x, y, w_a, h, group_a)
            AutoLayoutStrategy._recursive_weighted_split(x + w_a, y, w_b, h, group_b)
        else:
            h_a = h * split_pct
            h_b = h - h_a
            # Récursion
            AutoLayoutStrategy._recursive_weighted_split(x, y, w, h_a, group_a)
            AutoLayoutStrategy._recursive_weighted_split(x, y + h_a, w, h_b, group_b)
    @staticmethod
    def _mosaic_smart(tw, th, images):
        """
        Algorithme 'Justified Layout' :
        1. Calcule combien de lignes sont nécessaires pour remplir le ratio de l'écran.
        2. Distribue les images sur ces lignes.
        3. Ajuste la hauteur de chaque ligne pour qu'elle fasse exactement la largeur de l'écran.
        """
        if not images: return
        
        # 1. Calculer le 'Poids' total (somme des ratios)
        ratios = [img.current_aspect() for img in images]
        total_ratio = sum(ratios)
        
        # Ratio de la zone cible (L'écran)
        screen_ratio = tw / th
        
        # 2. Estimation du nombre de lignes idéal
        # Si on empile des lignes de ratio ~screen_ratio, alors:
        # Nombre de lignes ~ Racine(Total_Ratio / Screen_Ratio * N) ?? 
        # Plus simple : Si on met tout sur 1 ligne, ratio = Total. On veut ratio = Screen.
        # Donc on divise par K lignes. Moyenne ratio ligne = Total / K.
        # On veut Total / K ≈ Screen. Donc K ≈ Total / Screen.
        
        ideal_rows = round(total_ratio / screen_ratio)
        ideal_rows = max(1, ideal_rows) # Au moins 1 ligne
        
        # 3. Distribution gloutonne des images dans les lignes
        rows = []
        current_row = []
        current_row_ratio = 0.0
        
        # Ratio cible par ligne pour être équilibré
        avg_target_row_ratio = total_ratio / ideal_rows
        
        for i, img in enumerate(images):
            current_row.append(img)
            current_row_ratio += ratios[i]
            
            # Si la ligne est assez remplie (proche de la moyenne ou du ratio écran)
            # On coupe ici, sauf si c'est la dernière image
            if current_row_ratio >= avg_target_row_ratio and len(rows) < ideal_rows - 1:
                rows.append((current_row, current_row_ratio))
                current_row = []
                current_row_ratio = 0.0
        
        # Ajouter le reste dans la dernière ligne
        if current_row:
            rows.append((current_row, current_row_ratio))
            
        # 4. Calcul de la géométrie finale
        # On calcule la hauteur totale utilisée pour centrer verticalement si besoin
        total_used_height = 0
        
        # D'abord, on calcule la hauteur de chaque ligne pour qu'elle fasse largeur TW
        # W = H * Ratio => H = W / Ratio
        row_heights = []
        for r_imgs, r_ratio in rows:
            if r_ratio == 0: continue
            h = tw / r_ratio
            row_heights.append(h)
            total_used_height += h
            
        # Facteur d'échelle pour faire tenir tout ça dans TH (si ça dépasse)
        # On veut faire rentrer 'total_used_height' dans 'th'
        scale_factor = 1.0
        if total_used_height > th:
            scale_factor = th / total_used_height
        
        # Si ça ne remplit pas tout (trop petit), on peut choisir de centrer ou d'agrandir.
        # Ici on agrandit pour remplir (COVER) sauf si c'est vraiment trop étiré.
        # Pour le mode "Espace disponible", on va essayer de remplir TH si possible.
        elif total_used_height < th and total_used_height > 0:
             scale_factor = th / total_used_height

        # Position de départ Y (Centrage vertical si on ne scale pas à fond, mais ici on scale)
        current_y = (th - (total_used_height * scale_factor)) / 2
        
        for idx_row, (r_imgs, r_ratio) in enumerate(rows):
            # Hauteur de cette ligne (ajustée au scale global)
            h_raw = row_heights[idx_row]
            final_h = h_raw * scale_factor
            
            current_x = 0
            for img in r_imgs:
                # Largeur = Hauteur * Ratio
                # On utilise final_h pour que tout soit aligné
                w = final_h * img.current_aspect()
                
                img.x = current_x
                img.y = current_y
                img.w = int(w) + 1 # +1 pour éviter les micro-gaps d'arrondi
                img.h = int(final_h) + 1
                
                current_x += w
            
            current_y += final_h

    @staticmethod
    def _mosaic_bsp(x, y, w, h, images):
        """
        Partitionnement Binaire de l'Espace (BSP).
        Divise récursivement la zone (x,y,w,h) en 2 selon le poids des images.
        """
        if not images: return

        # Cas de base : 1 seule image -> Elle prend toute la place
        if len(images) == 1:
            img = images[0]
            img.x = int(x)
            img.y = int(y)
            AutoLayoutStrategy._apply_fit_inside(img, x, y, w, h)
            return

        # Décision : Couper Verticalement ou Horizontalement ?
        # On coupe généralement le côté le plus long du rectangle
        split_vertical = w > h

        # Calcul des "Poids" pour savoir où couper la liste des images
        # Si coupe Verticale (côte à côte) : Poids = Ratio (Largeur relative)
        # Si coupe Horizontale (empilé) : Poids = 1/Ratio (Hauteur relative)
        if split_vertical:
            weights = [img.current_aspect() for img in images]
        else:
            weights = [1.0 / img.current_aspect() for img in images]

        total_weight = sum(weights)
        half_weight = total_weight / 2.0
        
        # Trouver l'index de coupure pour équilibrer les poids ( ~ moitié / moitié )
        current_w = 0
        split_idx = 1
        best_diff = float('inf')

        # On cherche l'index qui divise le mieux la liste en deux masses égales
        for i in range(len(weights) - 1):
            current_w += weights[i]
            diff = abs(current_w - half_weight)
            if diff < best_diff:
                best_diff = diff
                split_idx = i + 1
            else:
                # Si la différence augmente, on a dépassé l'optimum
                break
        
        # Séparation des groupes
        group_a = images[:split_idx]
        group_b = images[split_idx:]
        
        weight_a = sum(weights[:split_idx])
        weight_total = sum(weights)
        
        # Ratio de surface pour le groupe A
        ratio_a = weight_a / weight_total if weight_total > 0 else 0.5

        if split_vertical:
            # Coupe sur la largeur (X)
            w_a = w * ratio_a
            w_b = w - w_a
            # Récursion Gauche
            AutoLayoutStrategy._mosaic_bsp(x, y, w_a, h, group_a)
            # Récursion Droite
            AutoLayoutStrategy._mosaic_bsp(x + w_a, y, w_b, h, group_b)
        else:
            # Coupe sur la hauteur (Y)
            h_a = h * ratio_a
            h_b = h - h_a
            # Récursion Haut
            AutoLayoutStrategy._mosaic_bsp(x, y, w, h_a, group_a)
            # Récursion Bas
            AutoLayoutStrategy._mosaic_bsp(x, y + h_a, w, h_b, group_b)

    @staticmethod
    def _justified_optimized(target_w, target_h, images):
        """
        Version "Fit Inside" stricte.
        Calcule le meilleur layout puis le réduit si nécessaire pour qu'il rentre
        intégralement dans l'écran, sans aucun dépassement.
        """
        if not images: return
        count = len(images)
        if count == 0: return

        ratios = [img.current_aspect() for img in images]
        best_layout = None
        min_waste = float('inf')

        # Tester différentes quantités de lignes
        max_test_rows = min(count, 30) 
        
        for n_rows in range(1, max_test_rows + 1):
            rows = []; current_row = []; current_r_sum = 0.0
            total_ratio = sum(ratios); target_row_r = total_ratio / n_rows
            
            img_idx = 0
            for r in range(n_rows):
                row_imgs = []; row_r_sum = 0.0
                while img_idx < count:
                    if r == n_rows - 1:
                        row_imgs.append(images[img_idx])
                        row_r_sum += ratios[img_idx]; img_idx += 1
                        continue
                    curr_img_r = ratios[img_idx]
                    dist_now = abs(target_row_r - row_r_sum)
                    dist_with = abs(target_row_r - (row_r_sum + curr_img_r))
                    if row_imgs and dist_with > dist_now: break
                    row_imgs.append(images[img_idx])
                    row_r_sum += curr_img_r; img_idx += 1
                if row_imgs: rows.append( {'imgs': row_imgs, 'sum': row_r_sum} )

            simulated_total_h = 0
            for row in rows:
                if row['sum'] > 0: simulated_total_h += target_w / row['sum']
            
            diff = abs(simulated_total_h - target_h)
            if diff < min_waste:
                min_waste = diff
                best_layout = {'rows': rows, 'total_h': simulated_total_h}

        if not best_layout: return

        # --- LOGIQUE CORRIGÉE ICI ---
        # On veut que le bloc final rentre dans (target_w, target_h).
        # Le bloc layout a une largeur théorique de target_w et une hauteur de best_layout['total_h'].
        
        # Scale X : on veut que width <= target_w -> target_w / target_w = 1.0
        # Scale Y : on veut que height <= target_h -> target_h / total_h
        
        # On prend le MINIMUM pour que les deux conditions soient vraies.
        scale_h = target_h / best_layout['total_h']
        final_scale = min(1.0, scale_h)
        
        final_block_w = target_w * final_scale
        final_block_h = best_layout['total_h'] * final_scale
        
        # Centrage
        start_x = (target_w - final_block_w) / 2
        start_y = (target_h - final_block_h) / 2
        
        current_y = start_y
        for row in best_layout['rows']:
            if row['sum'] == 0: continue
            raw_h = target_w / row['sum']
            display_h = raw_h * final_scale
            
            current_x = start_x
            for img in row['imgs']:
                display_w = display_h * img.current_aspect()
                img.x = current_x
                img.y = current_y
                # +1 pixel pour éviter les trous d'arrondi visuels, 
                # mais vu qu'on a un scale < 1.0, ça ne devrait pas dépasser l'écran.
                img.w = int(display_w) + 1 
                img.h = int(display_h) + 1
                img.crop_box_norm = (0.0, 0.0, 1.0, 1.0)
                current_x += display_w
            current_y += display_h
            
    # --- (Garder les autres méthodes Grid, Horizontal, Masonry si vous voulez) ---
    @staticmethod
    def _grid_cover(tw, th, images):
        # ... (Code existant inchangé) ...
        count = len(images)
        cols = math.ceil(math.sqrt(count))
        rows = math.ceil(count / cols)
        cw, ch = tw / cols, th / rows
        for i, img in enumerate(images):
            img.x = (i % cols) * cw
            img.y = (i // cols) * ch
            AutoLayoutStrategy._apply_crop_cover(img, cw, ch)

    @staticmethod
    def _horizontal_strip(tw, th, images):
        # ... (Code existant inchangé) ...
        x = 0
        for img in images:
            img.x = x; img.y = 0; img.h = int(th)
            img.w = int(th * img.current_aspect())
            img.crop_box_norm = (0.0, 0.0, 1.0, 1.0)
            x += img.w

    @staticmethod
    def _masonry(tw, th, images):
        # ... (Code existant inchangé) ...
        cols = max(3, int(tw / 500)); col_w = tw / cols; heights = [0] * cols
        for img in images:
            sc = heights.index(min(heights))
            nh = int(col_w / img.current_aspect())
            img.x = sc * col_w; img.y = heights[sc]; img.w, img.h = int(col_w), nh
            img.crop_box_norm = (0.0, 0.0, 1.0, 1.0)
            heights[sc] += nh
            
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