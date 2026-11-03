# ui.py
# ui.py
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter.filedialog import askopenfilenames
import tkinter.ttk as ttk
import os
import threading
import tempfile
import webbrowser
from PIL import ImageTk, Image

from image_tools import (
    LoadedImage, load_images_from_paths, AutoLayoutStrategy,
    compose_wallpaper_contain
)
from screen_splitter import (
    get_monitor_layout, split_wallpaper_by_monitors, 
    virtual_desktop_bbox, set_multi_wallpaper_windows
)
import locales
from locales import tr

SNAP_DIST = 25

UI_TEXT = {
    "library_title": {
        "en": "Imported images",
        "fr": "Images importees",
        "es": "Imagenes importadas",
        "de": "Importierte Bilder",
    },
    "library_empty": {
        "en": "Add images to start composing a wallpaper.",
        "fr": "Ajoutez des images pour commencer une composition.",
        "es": "Anade imagenes para empezar una composicion.",
        "de": "Fuge Bilder hinzu, um die Komposition zu starten.",
    },
    "library_count": {
        "en": "{} image(s)",
        "fr": "{} image(s)",
        "es": "{} imagen(es)",
        "de": "{} Bild(er)",
    },
    "project_actions": {
        "en": "Project",
        "fr": "Projet",
        "es": "Proyecto",
        "de": "Projekt",
    },
    "edit_mode": {
        "en": "Edit mode",
        "fr": "Mode edition",
        "es": "Modo de edicion",
        "de": "Bearbeitungsmodus",
    },
    "btn_new_project": {
        "en": "New project",
        "fr": "Nouveau projet",
        "es": "Nuevo proyecto",
        "de": "Neues Projekt",
    },
    "stage_title": {
        "en": "Composition stage",
        "fr": "Zone de composition",
        "es": "Zona de composicion",
        "de": "Kompositionsflache",
    },
    "stage_subtitle": {
        "en": "Move, scale, crop and arrange images inside the virtual desktop.",
        "fr": "Deplacez, redimensionnez, rognez et organisez les images dans le bureau virtuel.",
        "es": "Mueve, escala, recorta y organiza las imagenes dentro del escritorio virtual.",
        "de": "Bilder im virtuellen Desktop bewegen, skalieren, zuschneiden und anordnen.",
    },
    "output_title": {
        "en": "Output preview",
        "fr": "Apercu de sortie",
        "es": "Vista de salida",
        "de": "Ausgabevorschau",
    },
    "output_subtitle": {
        "en": "Live monitor result based on your current layout.",
        "fr": "Resultat moniteurs en direct selon votre layout actuel.",
        "es": "Resultado en monitores segun el layout actual.",
        "de": "Live-Ergebnis auf den Monitoren basierend auf dem aktuellen Layout.",
    },
    "inspector_title": {
        "en": "Inspector",
        "fr": "Inspecteur",
        "es": "Inspector",
        "de": "Inspektor",
    },
    "inspector_subtitle": {
        "en": "Selected image and project summary.",
        "fr": "Image selectionnee et resume du projet.",
        "es": "Imagen seleccionada y resumen del proyecto.",
        "de": "Ausgewahltes Bild und Projektzusammenfassung.",
    },
    "selected_image": {
        "en": "Selected image",
        "fr": "Image selectionnee",
        "es": "Imagen seleccionada",
        "de": "Ausgewahltes Bild",
    },
    "transform_title": {
        "en": "Transform",
        "fr": "Transformation",
        "es": "Transformacion",
        "de": "Transformation",
    },
    "project_title": {
        "en": "Project",
        "fr": "Projet",
        "es": "Proyecto",
        "de": "Projekt",
    },
    "no_selection": {
        "en": "No image selected",
        "fr": "Aucune image selectionnee",
        "es": "Ninguna imagen seleccionada",
        "de": "Kein Bild ausgewahlt",
    },
    "no_selection_hint": {
        "en": "Click an image on the stage or in the library.",
        "fr": "Cliquez une image sur la scene ou dans la bibliotheque.",
        "es": "Haz clic en una imagen en la escena o en la biblioteca.",
        "de": "Klicke ein Bild auf der Flache oder in der Bibliothek an.",
    },
    "position": {
        "en": "Position",
        "fr": "Position",
        "es": "Posicion",
        "de": "Position",
    },
    "size": {
        "en": "Size",
        "fr": "Taille",
        "es": "Tamano",
        "de": "Grosse",
    },
    "crop": {
        "en": "Visible area",
        "fr": "Zone visible",
        "es": "Zona visible",
        "de": "Sichtbarer Bereich",
    },
    "rotation": {
        "en": "Rotation",
        "fr": "Rotation",
        "es": "Rotacion",
        "de": "Drehung",
    },
    "layer": {
        "en": "Layer",
        "fr": "Calque",
        "es": "Capa",
        "de": "Ebene",
    },
    "mode_move": {
        "en": "Move",
        "fr": "Deplacer",
        "es": "Mover",
        "de": "Bewegen",
    },
    "mode_scale": {
        "en": "Scale",
        "fr": "Redimensionner",
        "es": "Escalar",
        "de": "Skalieren",
    },
    "mode_crop": {
        "en": "Crop",
        "fr": "Rogner",
        "es": "Recortar",
        "de": "Zuschneiden",
    },
    "btn_layer_back": {
        "en": "Back",
        "fr": "Arriere",
        "es": "Atras",
        "de": "Zuruck",
    },
    "btn_layer_front": {
        "en": "Forward",
        "fr": "Avant",
        "es": "Adelante",
        "de": "Nach vorn",
    },
    "layout_current": {
        "en": "Layout",
        "fr": "Layout",
        "es": "Layout",
        "de": "Layout",
    },
    "mode_current": {
        "en": "Mode",
        "fr": "Mode",
        "es": "Modo",
        "de": "Modus",
    },
    "zoom_current": {
        "en": "Zoom",
        "fr": "Zoom",
        "es": "Zoom",
        "de": "Zoom",
    },
    "images_count": {
        "en": "{} loaded image(s)",
        "fr": "{} image(s) chargee(s)",
        "es": "{} imagen(es) cargada(s)",
        "de": "{} Bild(er) geladen",
    },
    "library_selected": {
        "en": "Selected",
        "fr": "Selectionnee",
        "es": "Seleccionada",
        "de": "Ausgewahlt",
    },
    "library_ready": {
        "en": "Ready",
        "fr": "Prete",
        "es": "Lista",
        "de": "Bereit",
    },
    "canvas_empty": {
        "en": "Add images, choose a layout, then start composing.",
        "fr": "Ajoutez des images, choisissez un layout, puis composez.",
        "es": "Anade imagenes, elige un layout y empieza a componer.",
        "de": "Bilder hinzufugen, Layout wahlen und dann komponieren.",
    },
    "selection_empty": {
        "en": "No selection",
        "fr": "Aucune selection",
        "es": "Sin seleccion",
        "de": "Keine Auswahl",
    },
    "selection_hint": {
        "en": "Select an image, then move, scale or crop it on the stage.",
        "fr": "Selectionnez une image, puis deplacez-la, redimensionnez-la ou rognez-la sur la scene.",
        "es": "Selecciona una imagen y luego muevela, escalala o recortala en la escena.",
        "de": "Bild auswahlen und dann auf der Flache bewegen, skalieren oder zuschneiden.",
    },
    "selection_summary": {
        "en": "{}  •  {} x {}  •  layer {}/{}",
        "fr": "{}  •  {} x {}  •  calque {}/{}",
        "es": "{}  •  {} x {}  •  capa {}/{}",
        "de": "{}  •  {} x {}  •  Ebene {}/{}",
    },
    "output_summary": {
        "en": "{} monitor(s)  •  {}  •  {}%",
        "fr": "{} ecran(s)  •  {}  •  {}%",
        "es": "{} monitor(es)  •  {}  •  {}%",
        "de": "{} Monitor(e)  •  {}  •  {}%",
    },
    "project_reset_status": {
        "en": "New project ready",
        "fr": "Nouveau projet pret",
        "es": "Nuevo proyecto listo",
        "de": "Neues Projekt bereit",
    },
    "new_project_confirm": {
        "en": "Start a new project and remove all imported images?",
        "fr": "Demarrer un nouveau projet et supprimer toutes les images importees ?",
        "es": "Iniciar un nuevo proyecto y eliminar todas las imagenes importadas?",
        "de": "Neues Projekt starten und alle importierten Bilder entfernen?",
    },
}

class WallpaperApp:
    def __init__(self, root):
        self.root = root
        self.root.title(tr("app_title"))
        
        # Démarrage centré (80% taille écran)
        self._center_window()

        self.monitor_layout = get_monitor_layout()
        if self.monitor_layout:
            x0, y0, x1, y1 = virtual_desktop_bbox(self.monitor_layout)
            self.target_w = x1 - x0
            self.target_h = y1 - y0
        else:
            self.target_w = 1920
            self.target_h = 1080

        self.bg_color = (0, 0, 0)
        self.images = []; self.active_idx = None
        
        self.history = []; self.history_idx = -1
        self.zoom = 0.15; self.pan_x = 50; self.pan_y = 50
        
        self.mode = "move" # Renamed from interaction_mode for consistency
        self._drag_data = {"x": 0, "y": 0, "item": None, "action": None}
        self.show_monitors = tk.BooleanVar(value=True)
        self._sim_images = []
        self._library_thumbs = []
        self._inspector_thumb = None

        self.colors = {
            "bg": "#0b1120",
            "surface": "#11192b",
            "panel": "#162033",
            "panel_soft": "#101829",
            "panel_alt": "#1e2940",
            "canvas_bg": "#09111f",
            "accent": "#8ab4f8",
            "accent_glow": "#17324f",
            "accent_soft": "#1b3149",
            "accent_line": "#d9e7ff",
            "text": "#f7f9fd",
            "text_dim": "#b1bfd3",
            "text_muted": "#7d8ca3",
            "success": "#78d4a0",
            "danger": "#ff8a80",
            "border": "#314056",
            "border_soft": "#243246",
            "monitor": "#9ecbff",
            "thumb": "#0d1524"
        }

        self._setup_ui()
        self.root.update() # Ensure sizes are calculated
        self._auto_fit()
        self._save_state("Init")
        self._refresh_canvas()

        self.root.bind("<Control-z>", lambda e: self.cmd_undo())
        self.root.bind("<Control-y>", lambda e: self.cmd_redo())
        self.root.bind("<Delete>", lambda e: self.cmd_remove_img())

    def _center_window(self):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = int(sw * 0.8)
        h = int(sh * 0.8)
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _u(self, key, *args):
        lang = locales.get_current_language()
        text = UI_TEXT.get(key, {}).get(lang, UI_TEXT.get(key, {}).get("en", key))
        if args:
            return text.format(*args)
        return text

    def _make_card(self, parent, bg_key="panel", border_key="border"):
        return tk.Frame(
            parent,
            bg=self.colors[bg_key],
            highlightthickness=1,
            highlightbackground=self.colors[border_key],
            highlightcolor=self.colors[border_key],
            bd=0,
        )

    def _style_button(self, button, variant="outlined", active=False):
        if variant == "contained":
            button.config(
                bg=self.colors["accent"],
                fg=self.colors["canvas_bg"],
                activebackground=self.colors["accent_line"],
                activeforeground=self.colors["canvas_bg"],
                highlightthickness=0,
                bd=0,
                relief="flat",
            )
            return

        if variant == "tonal":
            bg = self.colors["accent_soft"] if active else self.colors["panel_alt"]
            fg = self.colors["accent_line"] if active else self.colors["text"]
            border = self.colors["accent"] if active else self.colors["border"]
            button.config(
                bg=bg,
                fg=fg,
                activebackground=bg,
                activeforeground=fg,
                highlightthickness=1,
                highlightbackground=border,
                highlightcolor=border,
                bd=0,
                relief="flat",
            )
            return

        button.config(
            bg=self.colors["panel_alt"],
            fg=self.colors["text"],
            activebackground=self.colors["panel"],
            activeforeground=self.colors["text"],
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["border"],
            bd=0,
            relief="flat",
        )

    def _make_contained_preview(self, img, width, height, bg_hex=None):
        bg_hex = bg_hex or self.colors["thumb"]
        im_rot = img.display_image.rotate(img.angle, expand=True, resample=Image.Resampling.NEAREST)
        rw, rh = im_rot.size
        cl, ct, cr, cb = img.crop_box_norm
        l, t = int(cl * rw), int(ct * rh)
        r, b = int(cr * rw), int(cb * rh)
        if r - l < 1:
            r = l + 1
        if b - t < 1:
            b = t + 1

        im_cropped = im_rot.crop((l, t, r, b))
        im_cropped.thumbnail((width, height), Image.Resampling.LANCZOS)

        preview = Image.new("RGBA", (width, height), bg_hex)
        px = (width - im_cropped.width) // 2
        py = (height - im_cropped.height) // 2
        preview.paste(im_cropped, (px, py), im_cropped)
        return ImageTk.PhotoImage(preview)

    def _setup_ui(self):
        self.status_var = tk.StringVar(value=tr("status_ready"))
        self.root.configure(bg=self.colors["bg"])
        self.root.minsize(1220, 790)

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "WallCraft.TCombobox",
            fieldbackground=self.colors["panel_alt"],
            background=self.colors["panel_alt"],
            foreground=self.colors["text"],
            arrowcolor=self.colors["accent"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
            insertcolor=self.colors["text"],
            padding=8,
        )
        style.map(
            "WallCraft.TCombobox",
            fieldbackground=[("readonly", self.colors["panel_alt"])],
            foreground=[("readonly", self.colors["text"])],
        )
        outlined_button = {
            "font": ("Segoe UI Semibold", 9),
            "padx": 14,
            "pady": 9,
            "cursor": "hand2",
            "disabledforeground": self.colors["text_muted"],
        }
        tonal_button = {
            "font": ("Segoe UI Semibold", 9),
            "padx": 12,
            "pady": 9,
            "cursor": "hand2",
            "disabledforeground": self.colors["text_muted"],
        }

        self._layout_ids = ["layout_mosaic", "layout_lines", "layout_grid", "layout_v_strip", "layout_h_strip", "layout_optimal"]

        shell = tk.Frame(self.root, bg=self.colors["bg"])
        shell.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

        topbar = self._make_card(shell, "surface")
        topbar.pack(fill=tk.X, pady=(0, 14))

        header_top = tk.Frame(topbar, bg=self.colors["surface"])
        header_top.pack(fill=tk.X, padx=18, pady=(16, 10))

        brand = tk.Frame(header_top, bg=self.colors["surface"])
        brand.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_title = tk.Label(brand, text=tr("app_title"), font=("Segoe UI Semibold", 22), bg=self.colors["surface"], fg=self.colors["text"])
        self.lbl_title.pack(anchor="w")
        self.lbl_sub = tk.Label(brand, text="", font=("Segoe UI", 9), bg=self.colors["surface"], fg=self.colors["text_dim"])
        self.lbl_sub.pack(anchor="w", pady=(5, 0))

        tag_style = {"fg": self.colors["text_muted"], "font": ("Segoe UI", 8, "bold")}

        toolbar = tk.Frame(topbar, bg=self.colors["surface"])
        toolbar.pack(fill=tk.X, padx=18, pady=(0, 16))

        lang_card = self._make_card(toolbar, "panel_alt", "border_soft")
        lang_card.pack(side=tk.LEFT, padx=(0, 10))
        lang_inner = tk.Frame(lang_card, bg=self.colors["panel_alt"])
        lang_inner.pack(padx=12, pady=10)
        self.lbl_lang_tag = tk.Label(lang_inner, bg=self.colors["panel_alt"], **tag_style)
        self.lbl_lang_tag.pack(anchor="w")
        self.combo_lang = ttk.Combobox(lang_inner, values=list(locales.LANGUAGES.values()), state="readonly", width=13, style="WallCraft.TCombobox")
        current_lang = locales.get_current_language()
        lang_keys = list(locales.LANGUAGES.keys())
        idx = lang_keys.index(current_lang) if current_lang in lang_keys else 0
        self.combo_lang.current(idx)
        self.combo_lang.pack(fill=tk.X, pady=(6, 0))
        self.combo_lang.bind("<<ComboboxSelected>>", self.on_lang_changed)

        project_group = self._make_card(toolbar, "panel_alt", "border_soft")
        project_group.pack(side=tk.LEFT, padx=(0, 10))
        project_inner = tk.Frame(project_group, bg=self.colors["panel_alt"])
        project_inner.pack(padx=12, pady=10)
        self.lbl_project_tag = tk.Label(project_inner, bg=self.colors["panel_alt"], **tag_style)
        self.lbl_project_tag.pack(anchor="w")
        project_actions = tk.Frame(project_inner, bg=self.colors["panel_alt"])
        project_actions.pack(fill=tk.X, pady=(8, 0))
        self.btn_new = tk.Button(project_actions, command=self.cmd_new_project, **outlined_button)
        self.btn_new.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_add = tk.Button(project_actions, command=self.cmd_add_images, **outlined_button)
        self.btn_add.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_auto = tk.Button(project_actions, command=self.cmd_autofill, **outlined_button)
        self.btn_auto.pack(side=tk.LEFT)

        layout_group = self._make_card(toolbar, "panel_alt", "border_soft")
        layout_group.pack(side=tk.LEFT, padx=(0, 10))
        layout_inner = tk.Frame(layout_group, bg=self.colors["panel_alt"])
        layout_inner.pack(padx=12, pady=10)
        self.lbl_layout_tag = tk.Label(layout_inner, bg=self.colors["panel_alt"], **tag_style)
        self.lbl_layout_tag.pack(anchor="w")
        self.combo_layout = ttk.Combobox(layout_inner, state="readonly", width=24, style="WallCraft.TCombobox")
        self.combo_layout.pack(fill=tk.X, pady=(6, 0))

        mode_group_card = self._make_card(toolbar, "panel_alt", "border_soft")
        mode_group_card.pack(side=tk.LEFT, padx=(0, 10))
        mode_group = tk.Frame(mode_group_card, bg=self.colors["panel_alt"])
        mode_group.pack(padx=12, pady=10)
        self.lbl_mode_tag = tk.Label(mode_group, bg=self.colors["panel_alt"], **tag_style)
        self.lbl_mode_tag.pack(anchor="w")
        mode_actions = tk.Frame(mode_group, bg=self.colors["panel_alt"])
        mode_actions.pack(fill=tk.X, pady=(8, 0))
        self.btn_mode_move = tk.Button(mode_actions, command=lambda: self.set_mode("move"), **tonal_button)
        self.btn_mode_move.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_mode_scale = tk.Button(mode_actions, command=lambda: self.set_mode("scale"), **tonal_button)
        self.btn_mode_scale.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_mode_crop = tk.Button(mode_actions, command=lambda: self.set_mode("crop"), **tonal_button)
        self.btn_mode_crop.pack(side=tk.LEFT)

        action_spacer = tk.Frame(toolbar, bg=self.colors["surface"])
        action_spacer.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_apply = tk.Button(
            toolbar,
            command=self.cmd_apply_wallpaper,
            font=("Segoe UI Semibold", 10),
            padx=22,
            pady=12,
            cursor="hand2",
        )
        self.btn_apply.pack(side=tk.RIGHT)

        content = tk.Frame(shell, bg=self.colors["bg"])
        content.pack(fill=tk.BOTH, expand=True)
        content.grid_columnconfigure(0, weight=0, minsize=272)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=self.colors["bg"], width=272)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_propagate(False)

        center = tk.Frame(content, bg=self.colors["bg"])
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(0, weight=5)
        center.grid_rowconfigure(1, weight=3)
        center.grid_columnconfigure(0, weight=1)

        library_card = self._make_card(left)
        library_card.pack(fill=tk.BOTH, expand=True)
        lib_header = tk.Frame(library_card, bg=self.colors["panel"])
        lib_header.pack(fill=tk.X, padx=18, pady=(18, 12))
        self.lbl_library_title = tk.Label(lib_header, bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI Semibold", 15))
        self.lbl_library_title.pack(anchor="w")
        self.lbl_library_count = tk.Label(lib_header, bg=self.colors["panel"], fg=self.colors["text_dim"], font=("Segoe UI", 9))
        self.lbl_library_count.pack(anchor="w", pady=(4, 0))

        library_body = tk.Frame(library_card, bg=self.colors["panel"])
        library_body.pack(fill=tk.BOTH, expand=True, padx=12)
        self.library_canvas = tk.Canvas(library_body, bg=self.colors["panel"], bd=0, highlightthickness=0, yscrollincrement=18)
        library_scroll = tk.Scrollbar(
            library_body,
            orient="vertical",
            command=self.library_canvas.yview,
            bg=self.colors["panel_alt"],
            troughcolor=self.colors["panel_soft"],
            activebackground=self.colors["accent_soft"],
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.library_canvas.configure(yscrollcommand=library_scroll.set)
        self.library_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        library_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.library_inner = tk.Frame(self.library_canvas, bg=self.colors["panel"])
        self._library_window = self.library_canvas.create_window((0, 0), window=self.library_inner, anchor="nw")
        self.library_inner.bind("<Configure>", self._on_library_inner_configure)
        self.library_canvas.bind("<Configure>", self._on_library_canvas_configure)

        lib_footer = tk.Frame(library_card, bg=self.colors["panel"])
        lib_footer.pack(fill=tk.X, padx=18, pady=(12, 16))
        action_row = tk.Frame(lib_footer, bg=self.colors["panel"])
        action_row.pack(fill=tk.X)
        self.btn_rem = tk.Button(action_row, command=self.cmd_remove_img, **outlined_button)
        self.btn_rem.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        layer_row = tk.Frame(action_row, bg=self.colors["panel"])
        layer_row.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_layer_back = tk.Button(layer_row, command=self.cmd_layer_backward, **tonal_button)
        self.btn_layer_back.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.btn_layer_front = tk.Button(layer_row, command=self.cmd_layer_forward, **tonal_button)
        self.btn_layer_front.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chk_monitors = tk.Checkbutton(
            lib_footer,
            variable=self.show_monitors,
            command=self._refresh_canvas,
            indicatoron=False,
            bg=self.colors["panel_alt"],
            fg=self.colors["text_dim"],
            activebackground=self.colors["panel_alt"],
            activeforeground=self.colors["text"],
            selectcolor=self.colors["panel_alt"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["border"],
            font=("Segoe UI Semibold", 10),
            padx=12,
            pady=10,
            cursor="hand2",
        )
        self.chk_monitors.pack(fill=tk.X, pady=(10, 10))
        status_row = tk.Frame(lib_footer, bg=self.colors["panel"])
        status_row.pack(fill=tk.X)
        self.lbl_status = tk.Label(status_row, textvariable=self.status_var, bg=self.colors["accent_soft"], fg=self.colors["accent_line"], font=("Segoe UI Semibold", 9), padx=10, pady=6)
        self.lbl_status.pack(side=tk.LEFT)
        self.btn_kofi = tk.Button(status_row, command=self.cmd_open_kofi, bg=self.colors["panel"], fg=self.colors["text_muted"], activebackground=self.colors["panel"], activeforeground=self.colors["accent"], bd=0, relief="flat", highlightthickness=0, font=("Segoe UI", 9), cursor="hand2")
        self.btn_kofi.pack(side=tk.RIGHT)

        stage_card = self._make_card(center)
        stage_card.grid(row=0, column=0, sticky="nsew")
        stage_header = tk.Frame(stage_card, bg=self.colors["panel"])
        stage_header.pack(fill=tk.X, padx=16, pady=(16, 10))
        stage_titles = tk.Frame(stage_header, bg=self.colors["panel"])
        stage_titles.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_stage_title = tk.Label(stage_titles, bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI Semibold", 16))
        self.lbl_stage_title.pack(anchor="w")
        self.lbl_stage_sub = tk.Label(stage_titles, bg=self.colors["panel"], fg=self.colors["text_dim"], font=("Segoe UI", 9))
        self.lbl_stage_sub.pack(anchor="w", pady=(4, 0))
        stage_badges = tk.Frame(stage_header, bg=self.colors["panel"])
        stage_badges.pack(side=tk.RIGHT, anchor="ne")
        self.lbl_stage_meta = tk.Label(stage_badges, bg=self.colors["accent_soft"], fg=self.colors["accent_line"], font=("Segoe UI Semibold", 9), padx=12, pady=6)
        self.lbl_stage_meta.pack(anchor="e")
        self.lbl_stage_hint = tk.Label(stage_badges, bg=self.colors["panel"], fg=self.colors["text_dim"], font=("Segoe UI", 9))
        self.lbl_stage_hint.pack(anchor="e", pady=(6, 0))

        canvas_shell = self._make_card(stage_card, "panel_soft", "border_soft")
        canvas_shell.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.canvas = tk.Canvas(canvas_shell, bg=self.colors["canvas_bg"], highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        output_card = self._make_card(center)
        output_card.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        output_header = tk.Frame(output_card, bg=self.colors["panel"])
        output_header.pack(fill=tk.X, padx=16, pady=(16, 10))
        output_titles = tk.Frame(output_header, bg=self.colors["panel"])
        output_titles.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_output_title = tk.Label(output_titles, bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI Semibold", 15))
        self.lbl_output_title.pack(anchor="w")
        self.lbl_output_sub = tk.Label(output_titles, bg=self.colors["panel"], fg=self.colors["text_dim"], font=("Segoe UI", 9))
        self.lbl_output_sub.pack(anchor="w", pady=(4, 0))
        self.lbl_output_meta = tk.Label(output_header, bg=self.colors["panel_alt"], fg=self.colors["accent_line"], font=("Segoe UI Semibold", 9), padx=12, pady=6)
        self.lbl_output_meta.pack(side=tk.RIGHT, anchor="ne")

        sim_shell = self._make_card(output_card, "panel_soft", "border_soft")
        sim_shell.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.sim_canvas = tk.Canvas(sim_shell, bg=self.colors["panel_soft"], highlightthickness=0)
        self.sim_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for button in (self.btn_new, self.btn_add, self.btn_auto, self.btn_rem):
            self._style_button(button, "outlined")
        for button in (self.btn_mode_move, self.btn_mode_scale, self.btn_mode_crop, self.btn_layer_back, self.btn_layer_front):
            self._style_button(button, "tonal")
        self._style_button(self.btn_apply, "contained")

        self._refresh_texts()
        self.combo_layout.current(0)

        self.canvas.bind("<ButtonPress-1>", self.on_left_down)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_up)
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonPress-3>", self.on_pan_start)
        self.canvas.bind("<B3-Motion>", self.on_pan_drag)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom)
        self.canvas.bind("<Button-5>", self.on_zoom)
        self.sim_canvas.bind("<Configure>", lambda e: self._refresh_sim_view())

    def _on_library_inner_configure(self, _event=None):
        self.library_canvas.configure(scrollregion=self.library_canvas.bbox("all"))

    def _on_library_canvas_configure(self, event):
        self.library_canvas.itemconfigure(self._library_window, width=event.width)

    def _select_image(self, idx):
        if 0 <= idx < len(self.images):
            self.active_idx = idx
            self._refresh_library_panel()
            self._refresh_canvas()

    def on_lang_changed(self, event):
        idx = self.combo_lang.current()
        if idx >= 0:
            lang_code = list(locales.LANGUAGES.keys())[idx]
            locales.set_language(lang_code)
            self._refresh_texts()
            
    def _refresh_texts(self):
        self.root.title(tr("app_title"))
        self.lbl_title.config(text=tr("app_title"))
        self.lbl_lang_tag.config(text=tr("lang_select"))
        self.lbl_project_tag.config(text=self._u("project_actions"))
        self.lbl_layout_tag.config(text=tr("lbl_layout"))
        self.lbl_mode_tag.config(text=self._u("edit_mode"))

        idx = self.combo_layout.current()
        new_layouts = [tr(l_id) for l_id in self._layout_ids]
        self.combo_layout.config(values=new_layouts)
        if idx >= 0:
            self.combo_layout.current(idx)

        self.btn_new.config(text=self._u("btn_new_project"))
        self.btn_add.config(text=tr("btn_add_images"))
        self.btn_auto.config(text=tr("btn_auto_arrange"))
        self.btn_rem.config(text=tr("btn_remove"))
        self.btn_layer_back.config(text=self._u("btn_layer_back"))
        self.btn_layer_front.config(text=self._u("btn_layer_front"))
        self.btn_kofi.config(text=tr("btn_kofi"))
        self.btn_apply.config(text=tr("btn_apply"))
        self.chk_monitors.config(text=tr("chk_show_monitors"))

        self.lbl_library_title.config(text=self._u("library_title"))
        self.lbl_stage_title.config(text=self._u("stage_title"))
        self.lbl_stage_sub.config(text=self._u("stage_subtitle"))
        self.lbl_output_title.config(text=self._u("output_title"))
        self.lbl_output_sub.config(text=self._u("output_subtitle"))

        self._refresh_mode_buttons()
        self._refresh_header_summary()
        self._refresh_library_panel()
        self._refresh_inspector_panel()

    def _refresh_mode_buttons(self):
        buttons = (
            ("move", self.btn_mode_move, self._u("mode_move")),
            ("scale", self.btn_mode_scale, self._u("mode_scale")),
            ("crop", self.btn_mode_crop, self._u("mode_crop")),
        )
        for mode, button, label in buttons:
            button.config(text=label)
            self._style_button(button, "tonal", active=self.mode == mode)

    def _refresh_action_states(self):
        has_selection = self.active_idx is not None and 0 <= self.active_idx < len(self.images)
        self.btn_rem.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.btn_layer_back.config(state=tk.NORMAL if has_selection and self.active_idx > 0 else tk.DISABLED)
        self.btn_layer_front.config(
            state=tk.NORMAL if has_selection and self.active_idx < len(self.images) - 1 else tk.DISABLED
        )

    def _refresh_header_summary(self):
        screen_count = len(self.monitor_layout) if self.monitor_layout else 0
        self.lbl_sub.config(
            text=f"{self.target_w} x {self.target_h}  •  {tr('monitors_count', screen_count)}  •  {self._u('images_count', len(self.images))}"
        )

    def _refresh_library_panel(self):
        for child in self.library_inner.winfo_children():
            child.destroy()

        self._library_thumbs = []
        self.lbl_library_count.config(text=self._u("library_count", len(self.images)))
        self._refresh_action_states()

        if not self.images:
            empty = tk.Label(
                self.library_inner,
                text=self._u("library_empty"),
                bg=self.colors["panel"],
                fg=self.colors["text_muted"],
                font=("Segoe UI", 10),
                wraplength=190,
                justify=tk.LEFT,
                padx=8,
                pady=18,
            )
            empty.pack(fill=tk.X, padx=4, pady=(6, 10))
            return

        thumb_w = max(178, self.library_canvas.winfo_width() - 44)
        thumb_h = 72
        for idx, img in enumerate(self.images):
            active = idx == self.active_idx
            bg = self.colors["panel_alt"] if active else self.colors["panel_soft"]
            border = self.colors["accent"] if active else self.colors["border_soft"]

            item = tk.Frame(
                self.library_inner,
                bg=bg,
                highlightthickness=1,
                highlightbackground=border,
                highlightcolor=border,
                bd=0,
            )
            item.pack(fill=tk.X, padx=4, pady=(0, 10))

            thumb = self._make_contained_preview(img, thumb_w, thumb_h)
            self._library_thumbs.append(thumb)
            thumb_label = tk.Label(item, image=thumb, bg=bg, bd=0)
            thumb_label.pack(fill=tk.X, padx=10, pady=(10, 8))

            title = tk.Label(
                item,
                text=os.path.basename(img.path),
                bg=bg,
                fg=self.colors["text"],
                font=("Segoe UI Semibold", 10),
                anchor="w",
                justify=tk.LEFT,
                wraplength=thumb_w,
            )
            title.pack(fill=tk.X, padx=10)

            ow, oh = img.original_image.size
            meta = tk.Label(
                item,
                text=f"{ow} x {oh}px  •  {img.z_index + 1}/{len(self.images)}",
                bg=bg,
                fg=self.colors["text_dim"],
                font=("Segoe UI", 9),
                anchor="w",
            )
            meta.pack(fill=tk.X, padx=10, pady=(2, 0))

            badge = tk.Label(
                item,
                text=self._u("library_selected") if active else self._u("library_ready"),
                bg=self.colors["accent_soft"] if active else self.colors["panel"],
                fg=self.colors["accent_line"] if active else self.colors["text_dim"],
                font=("Segoe UI Semibold", 8),
                padx=8,
                pady=4,
            )
            badge.pack(anchor="w", padx=10, pady=(8, 10))

            for widget in (item, thumb_label, title, meta, badge):
                widget.bind("<Button-1>", lambda _e, i=idx: self._select_image(i))

    def _get_mode_name(self):
        lang = locales.get_current_language()
        return {
            "en": {"move": "Move", "scale": "Scale", "crop": "Crop"},
            "fr": {"move": "Deplacer", "scale": "Redimensionner", "crop": "Rogner"},
            "es": {"move": "Mover", "scale": "Escalar", "crop": "Recortar"},
            "de": {"move": "Bewegen", "scale": "Skalieren", "crop": "Zuschneiden"},
        }.get(lang, {"move": "Move", "scale": "Scale", "crop": "Crop"})[self.mode]

    def _refresh_inspector_panel(self):
        screen_count = len(self.monitor_layout) if self.monitor_layout else 0
        layout_name = self.combo_layout.get() if self.combo_layout.get() else tr(self._layout_ids[0])
        mode_name = self._get_mode_name()

        if self.active_idx is None or self.active_idx >= len(self.images):
            self.lbl_stage_meta.config(text=self._u("selection_empty"))
            self.lbl_stage_hint.config(text=self._u("selection_hint"))
        else:
            img = self.images[self.active_idx]
            name = os.path.basename(img.path)
            if len(name) > 34:
                name = f"{name[:16]}...{name[-12:]}"
            self.lbl_stage_meta.config(
                text=self._u(
                    "selection_summary",
                    name,
                    int(img.w),
                    int(img.h),
                    img.z_index + 1,
                    max(1, len(self.images)),
                )
            )
            self.lbl_stage_hint.config(
                text=(
                    f"{mode_name}  •  "
                    f"{self._u('position')}: {int(img.x)}, {int(img.y)}  •  "
                    f"{self._u('crop')}: {int((img.crop_box_norm[2] - img.crop_box_norm[0]) * 100)}%"
                )
            )

        self.lbl_output_meta.config(text=self._u("output_summary", screen_count, layout_name, int(self.zoom * 100)))
        
    def set_mode(self, mode):
        if mode not in ("move", "scale", "crop"):
            return
        self.mode = mode
        self._refresh_texts()
        self._refresh_canvas()

    def toggle_mode(self):
        order = ("move", "scale", "crop")
        next_idx = (order.index(self.mode) + 1) % len(order)
        self.set_mode(order[next_idx])

    def cmd_apply_wallpaper(self):
        self.status_var.set(tr("status_processing"))
        self.root.update()
        try:
            # Rendu HD
            final = compose_wallpaper_contain((self.target_w, self.target_h), self.images, self.bg_color)
            tmp = os.path.join(tempfile.gettempdir(), "wallcraft_split")
            if not os.path.exists(tmp): os.makedirs(tmp)
            
            # Split
            results = split_wallpaper_by_monitors(final, self.monitor_layout, tmp, "screen")
            if not results: return messagebox.showerror(tr("error_title"), tr("err_no_monitors"))

            # Apply COM
            if set_multi_wallpaper_windows(results):
                messagebox.showinfo(tr("info_title"), tr("msg_apply_ok"))
            else:
                messagebox.showerror(tr("error_title"), tr("err_api_fail"))
        except Exception as e: 
            messagebox.showerror(tr("error_title"), str(e))
        finally: 
            self.status_var.set(tr("status_ready"))

    def cmd_new_project(self):
        if self.images and not messagebox.askyesno(tr("app_title"), self._u("new_project_confirm")):
            return

        self.images = []
        self.active_idx = None
        self.history = []
        self.history_idx = -1
        self.mode = "move"
        self._drag_data = {"x": 0, "y": 0, "item": None, "action": None}
        self.status_var.set(self._u("project_reset_status"))
        self.root.update_idletasks()
        self._auto_fit()
        self._save_state("Init")
        self._refresh_texts()
        self._refresh_canvas()

    def cmd_open_kofi(self):
        webbrowser.open("https://ko-fi.com/D1D21VSKW5")

    def _save_state(self, n):
        if self.history_idx < len(self.history)-1: self.history = self.history[:self.history_idx+1]
        self.history.append([i.clone() for i in self.images]); self.history_idx += 1
        if len(self.history)>20: self.history.pop(0); self.history_idx -= 1

    def cmd_undo(self):
        if self.history_idx>0: self.history_idx-=1; self._restore()
    def cmd_redo(self):
        if self.history_idx<len(self.history)-1: self.history_idx+=1; self._restore()
    def _restore(self):
        self.images = [i.clone() for i in self.history[self.history_idx]]
        self.active_idx = None
        self._refresh_library_panel()
        self._refresh_canvas()
    
    def _sync_z_indices(self):
        """Assure que les indices Z correspondent à l'ordre de la liste pour le rendu"""
        for i, img in enumerate(self.images):
            img.z_index = i

    def screen_to_logic(self, sx, sy): return (sx-self.pan_x)/self.zoom, (sy-self.pan_y)/self.zoom
    def logic_to_screen(self, lx, ly): return (lx*self.zoom)+self.pan_x, (ly*self.zoom)+self.pan_y

    def _refresh_canvas(self):
        self._refresh_header_summary()
        self._refresh_main_canvas()
        self._refresh_sim_view()
        self._refresh_inspector_panel()

    def _refresh_main_canvas(self):
        self.canvas.delete("all")
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        self.canvas.create_rectangle(0, 0, cw, ch, fill=self.colors["canvas_bg"], outline="")

        bx, by = self.logic_to_screen(0, 0)
        bw, bh = self.target_w * self.zoom, self.target_h * self.zoom
        shadow_pad = 18
        self.canvas.create_rectangle(
            bx - shadow_pad,
            by - shadow_pad,
            bx + bw + shadow_pad,
            by + bh + shadow_pad,
            fill="#0c1422",
            outline="",
            stipple="gray25",
        )
        self.canvas.create_rectangle(bx, by, bx + bw, by + bh, fill="#0d1626", outline="")

        grid_step = max(26, int(220 * self.zoom))
        x = int(bx - (bx % grid_step))
        while x < bx + bw:
            self.canvas.create_line(x, max(0, by), x, min(ch, by + bh), fill="#1b2536")
            x += grid_step

        y = int(by - (by % grid_step))
        while y < by + bh:
            self.canvas.create_line(max(0, bx), y, min(cw, bx + bw), y, fill="#1b2536")
            y += grid_step

        self.canvas.create_rectangle(bx, by, bx + bw, by + bh, fill="", outline=self.colors["border"], width=2)
        self.canvas.create_text(
            bx + 16,
            by + 14,
            text="STAGE",
            fill=self.colors["text_muted"],
            anchor="nw",
            font=("Segoe UI", 9, "bold"),
        )

        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        for idx, img in sorted(enumerate(self.images), key=lambda x:x[1].z_index):
            sw, sh = int(img.w*self.zoom), int(img.h*self.zoom)
            sx, sy = self.logic_to_screen(img.x, img.y)
            if sx>cw or sy>ch or sx+sw<0 or sy+sh<0: continue
            tk_img = img.get_tk_image(sw, sh)
            if tk_img:
                self.canvas.create_rectangle(sx + 4, sy + 6, sx + sw + 4, sy + sh + 6, fill="#04070d", outline="", stipple="gray50")
                self.canvas.create_image(sx, sy, image=tk_img, anchor="nw")
                if idx==self.active_idx:
                    self.canvas.create_rectangle(sx - 3, sy - 3, sx + sw + 3, sy + sh + 3, outline=self.colors["accent_line"], width=1)
                    self.canvas.create_rectangle(sx, sy, sx+sw, sy+sh, outline=self.colors["accent"], width=2)
                    if self.mode in ("crop", "scale"):
                        self._draw_handles(sx, sy, sw, sh)

        if self.show_monitors.get() and self.monitor_layout:
            vx, vy, _, _ = virtual_desktop_bbox(self.monitor_layout)
            for m in self.monitor_layout:
                mx, my = self.logic_to_screen(m["x"]-vx, m["y"]-vy)
                mw, mh = m["width"]*self.zoom, m["height"]*self.zoom
                self.canvas.create_rectangle(mx, my, mx+mw, my+mh, outline=self.colors["monitor"], dash=(6, 4), width=2)
                self.canvas.create_rectangle(mx + 10, my + 10, mx + 110, my + 30, fill="#0e2236", outline="")
                self.canvas.create_text(mx+16, my+20, text=m.get("name",""), fill=self.colors["monitor"], anchor="w", font=("Segoe UI", 8, "bold"))

        if not self.images:
            self.canvas.create_text(
                cw / 2,
                ch / 2,
                text=self._u("canvas_empty"),
                fill=self.colors["text_muted"],
                font=("Segoe UI", 12),
                width=max(260, cw - 160),
            )

    def _auto_fit(self):
        """Automatically adjusts zoom and offset to fit the virtual desktop in the canvas."""
        self.root.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 50 or ch < 50: return # Too small/not rendered yet

        vw, vh = self.target_w, self.target_h
        
        # Fit with tighter padding to make the stage more prominent.
        scale = min((cw * 0.95) / vw, (ch * 0.94) / vh)
        self.zoom = scale
        
        # Center
        self.pan_x = (cw - vw * scale) / 2
        self.pan_y = (ch - vh * scale) / 2
        self._refresh_canvas()

    def _refresh_sim_view(self):
        self.sim_canvas.delete("all")
        self._sim_images = []
        if not self.monitor_layout:
            return

        cw, ch = self.sim_canvas.winfo_width(), self.sim_canvas.winfo_height()
        if cw < 10 or ch < 10:
            return

        desk_y = ch * 0.8
        for y in range(ch):
            if y < desk_y:
                mix = y / max(1, desk_y)
                r = int(8 + (18 - 8) * mix)
                g = int(14 + (28 - 14) * mix)
                b = int(28 + (48 - 28) * mix)
            else:
                mix = (y - desk_y) / max(1, ch - desk_y)
                r = int(20 + (10 - 20) * mix)
                g = int(24 + (12 - 24) * mix)
                b = int(32 + (16 - 32) * mix)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.sim_canvas.create_line(0, y, cw, y, fill=color)

        self.sim_canvas.create_line(0, desk_y, cw, desk_y, fill="#485262", width=1)
        self.sim_canvas.create_rectangle(0, desk_y, cw, ch, fill="#121821", outline="")
        self.sim_canvas.create_line(0, desk_y + 1, cw, desk_y + 1, fill="#2c3748", width=1)
        self.sim_canvas.create_line(0, desk_y + 36, cw, desk_y + 36, fill="#0c1118", width=1)

        vx0, vy0, vx1, vy1 = virtual_desktop_bbox(self.monitor_layout)
        vw, vh = vx1 - vx0, vy1 - vy0

        gap_units = 180
        sorted_monitors = sorted(self.monitor_layout, key=lambda m: (m["x"], m["y"]))
        rank_by_id = {id(m): idx for idx, m in enumerate(sorted_monitors)}
        preview_span = vw + max(0, len(self.monitor_layout) - 1) * gap_units

        padding_x = 28
        padding_top = 16
        usable_h = max(80, desk_y - padding_top - 26)
        scale = min((cw - padding_x * 2) / max(1, preview_span), usable_h / max(1, vh))
        ox = (cw - preview_span * scale) / 2
        oy = padding_top + (usable_h - vh * scale) / 2

        for m in self.monitor_layout:
            gap_offset = rank_by_id[id(m)] * gap_units
            mx = ((m["x"] - vx0) + gap_offset) * scale + ox
            my = (m["y"] - vy0) * scale + oy
            mw = m["width"] * scale
            mh = m["height"] * scale

            self.sim_canvas.create_rectangle(mx + 7, my + 10, mx + mw + 7, my + mh + 12, fill="#05070b", outline="", stipple="gray50")
            self.sim_canvas.create_rectangle(mx - 6, my - 6, mx + mw + 6, my + mh + 6, fill="#151920", outline="#262d37", width=1)
            self.sim_canvas.create_rectangle(mx - 2, my - 2, mx + mw + 2, my + mh + 2, fill="#1e242d", outline="#3a4554", width=1)

            sx0, sy0 = mx + 4, my + 4
            sx1, sy1 = mx + mw - 4, my + mh - 4
            self.sim_canvas.create_rectangle(sx0, sy0, sx1, sy1, fill="#030405", outline="")

            for img in sorted(self.images, key=lambda x: x.z_index):
                ix0, iy0 = img.x, img.y
                ix1, iy1 = img.x + img.w, img.y + img.h
                mx0, my0 = m["x"] - vx0, m["y"] - vy0
                mx1, my1 = mx0 + m["width"], my0 + m["height"]

                if ix0 < mx1 and ix1 > mx0 and iy0 < my1 and iy1 > my0:
                    cx0 = max(0, mx0 - ix0)
                    cy0 = max(0, my0 - iy0)
                    cx1 = min(img.w, mx1 - ix0)
                    cy1 = min(img.h, my1 - iy0)

                    tx = sx0 + max(0, ix0 - mx0) * scale
                    ty = sy0 + max(0, iy0 - my0) * scale
                    tw = (cx1 - cx0) * scale
                    th = (cy1 - cy0) * scale

                    tk_slice = img.get_tk_image_slice(cx0, cy0, cx1, cy1, int(tw), int(th))
                    if tk_slice:
                        self.sim_canvas.create_image(tx, ty, image=tk_slice, anchor="nw")
                        self._sim_images.append(tk_slice)

            self.sim_canvas.create_line(sx0, sy0 + 1, sx1, sy0 + 1, fill="#5f6979")
            self.sim_canvas.create_rectangle(sx0, sy0, sx1, sy1, outline="#0b0e13", width=1)

            chip_w = min(120, max(74, mw * 0.32))
            self.sim_canvas.create_rectangle(mx + 12, my + 12, mx + 12 + chip_w, my + 30, fill="#232b36", outline="")
            self.sim_canvas.create_text(mx + 18, my + 21, text=m.get("name", ""), fill="#cfd6e0", anchor="w", font=("Segoe UI", 8, "bold"))

            stand_x = mx + mw / 2
            self.sim_canvas.create_rectangle(stand_x - 7, sy1 + 4, stand_x + 7, desk_y - 7, fill="#171b22", outline="#0c0f14")
            self.sim_canvas.create_rectangle(stand_x - 30, desk_y - 7, stand_x + 30, desk_y + 5, fill="#11151b", outline="#2a313c")
            self.sim_canvas.create_rectangle(mx + mw * 0.16, desk_y + 10, mx + mw * 0.84, desk_y + 22, fill="#090c11", outline="", stipple="gray50")
            
    def _draw_handles(self, x, y, w, h):
        s = 10
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        for px, py in pts:
            self.canvas.create_oval(
                px - s / 2,
                py - s / 2,
                px + s / 2,
                py + s / 2,
                fill=self.colors["accent"],
                outline=self.colors["accent_line"],
                width=2,
            )

    def on_zoom(self, e):
        f = 1.1 if (e.num==4 or e.delta>0) else 0.9
        mx, my = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        lx, ly = self.screen_to_logic(mx, my)
        self.zoom = max(0.01, min(self.zoom, 10.0))*f
        self.pan_x = mx - lx*self.zoom; self.pan_y = my - ly*self.zoom
        self._refresh_canvas()

    def on_pan_start(self, e): self._drag_data.update({"action":"pan", "lx":e.x, "ly":e.y}); self.canvas.config(cursor="fleur")
    def on_pan_drag(self, e):
        self.pan_x += e.x - self._drag_data["lx"]; self.pan_y += e.y - self._drag_data["ly"]
        self._drag_data.update({"lx":e.x, "ly":e.y}); self._refresh_canvas()

    def on_left_down(self, e):
        mx, my = e.x, e.y; lx, ly = self.screen_to_logic(mx, my)
        if self.mode in ("crop", "scale") and self.active_idx is not None:
            img = self.images[self.active_idx]
            sx, sy = self.logic_to_screen(img.x, img.y); sw, sh = img.w*self.zoom, img.h*self.zoom
            h = {"tl":(sx,sy),"tr":(sx+sw,sy),"br":(sx+sw,sy+sh),"bl":(sx,sy+sh)}
            for t, (hx,hy) in h.items():
                if abs(mx-hx)<10 and abs(my-hy)<10:
                    action = "resize_" + t if self.mode == "crop" else "scale_" + t
                    drag_data = {"action": action, "item": self.active_idx, "slx": lx, "sly": ly}
                    if self.mode == "scale":
                        drag_data.update(
                            {
                                "ox": img.x,
                                "oy": img.y,
                                "ow": img.w,
                                "oh": img.h,
                                "aspect": max(0.01, img.w / max(1, img.h)),
                            }
                        )
                    self._drag_data.update(drag_data)
                    return

        previous_active = self.active_idx
        clicked = None; max_z = -1
        for i, img in enumerate(self.images):
            if img.x<=lx<=img.x+img.w and img.y<=ly<=img.y+img.h:
                if img.z_index>max_z: max_z=img.z_index; clicked=i
        self.active_idx = clicked
        if clicked is not None:
            img = self.images[clicked]
            if self.mode == "scale":
                self._drag_data.update({"action": None, "item": clicked})
            else:
                self._drag_data.update({"action":"move", "item":clicked, "slx":lx, "sly":ly, "ox":img.x, "oy":img.y})
        else: self.on_pan_start(e)
        if previous_active != self.active_idx:
            self._refresh_library_panel()
        self._refresh_canvas()

    def on_left_drag(self, e):
        if not self._drag_data["action"]: return
        if self._drag_data["action"]=="pan": self.on_pan_drag(e); return
        lx, ly = self.screen_to_logic(e.x, e.y)
        img = self.images[self._drag_data["item"]]
        
        if self._drag_data["action"]=="move":
            nx, ny = self._drag_data["ox"]+(lx-self._drag_data["slx"]), self._drag_data["oy"]+(ly-self._drag_data["sly"])
            if not (e.state & 0x0001):
                if abs(nx)<SNAP_DIST: nx=0
                if abs(ny)<SNAP_DIST: ny=0
                for o in self.images:
                    if o is img: continue
                    if abs(nx-o.x)<SNAP_DIST: nx=o.x
                    if abs(nx-(o.x+o.w))<SNAP_DIST: nx=o.x+o.w
            img.x, img.y = nx, ny

        elif "resize" in self._drag_data["action"]:
            l, t, r, b = img.crop_box_norm
            w_vis, h_vis = max(1, img.w*self.zoom), max(1, img.h*self.zoom)
            dx_pct = ((e.x - self.logic_to_screen(self._drag_data["slx"],0)[0]) / w_vis) * (r-l)
            dy_pct = ((e.y - self.logic_to_screen(0,self._drag_data["sly"])[1]) / h_vis) * (b-t)
            a = self._drag_data["action"]
            if "tl" in a: l+=dx_pct; t+=dy_pct
            elif "br" in a: r+=dx_pct; b+=dy_pct
            elif "tr" in a: r+=dx_pct; t+=dy_pct
            elif "bl" in a: l+=dx_pct; b+=dy_pct
            img.crop_box_norm = (max(0,min(l,r-0.05)), max(0,min(t,b-0.05)), min(1,max(r,l+0.05)), min(1,max(b,t+0.05)))
            self._drag_data.update({"slx":lx, "sly":ly})
        elif "scale" in self._drag_data["action"]:
            aspect = self._drag_data.get("aspect", 1.0)
            opposite = {
                "scale_tl": ("br", self._drag_data["ox"] + self._drag_data["ow"], self._drag_data["oy"] + self._drag_data["oh"]),
                "scale_tr": ("bl", self._drag_data["ox"], self._drag_data["oy"] + self._drag_data["oh"]),
                "scale_br": ("tl", self._drag_data["ox"], self._drag_data["oy"]),
                "scale_bl": ("tr", self._drag_data["ox"] + self._drag_data["ow"], self._drag_data["oy"]),
            }
            corner, ax, ay = opposite[self._drag_data["action"]]
            raw_w = abs(lx - ax)
            raw_h = abs(ly - ay)
            new_w = max(40.0, raw_w, raw_h * aspect)
            new_h = max(40.0, new_w / aspect)
            new_w = max(40, int(round(new_w)))
            new_h = max(40, int(round(new_h)))

            if corner == "tl":
                img.x, img.y = ax, ay
            elif corner == "tr":
                img.x, img.y = ax - new_w, ay
            elif corner == "bl":
                img.x, img.y = ax, ay - new_h
            else:
                img.x, img.y = ax - new_w, ay - new_h

            img.w = new_w
            img.h = new_h
        self._refresh_canvas()

    def on_left_up(self, e):
        action = self._drag_data["action"]
        if action and action!="pan":
            self._save_state(action)
            if "resize" in action or "scale" in action:
                self._refresh_library_panel()
        self._drag_data["action"]=None; self.canvas.config(cursor="crosshair")

    def cmd_add_images(self):
        p = askopenfilenames(filetypes=[(tr("filetype_images"), "*.jpg;*.png;*.webp;*.jpeg")])
        if p:
            ni = load_images_from_paths(p)
            self.root.update_idletasks()
            cw = max(1, self.canvas.winfo_width())
            ch = max(1, self.canvas.winfo_height())
            center_lx, center_ly = self.screen_to_logic(cw * 0.5, ch * 0.5)
            for i,m in enumerate(ni):
                m.w = 600
                m.h = int(600 / m.current_aspect())
                m.x = center_lx - (m.w * 0.5) + (40 * i)
                m.y = center_ly - (m.h * 0.5) + (26 * i)
                m.z_index = len(self.images)+i
            self.images.extend(ni)
            self.active_idx = len(self.images) - 1 if self.images else None
            self._save_state("Add")
            self._refresh_library_panel()
            self._refresh_canvas()
            
    def cmd_autofill(self):
        self._save_state("Auto")
        idx = self.combo_layout.current()
        if idx == -1: return
        layout_id = self._layout_ids[idx]
        
        if layout_id == "layout_optimal":
            pass # Performance warning removed as requested
            
        # If the mode is 'Perfect Mosaic' (the intelligent default), handle the case of 1 image/screen
        if layout_id == "layout_mosaic":
            monitors = self.monitor_layout
            if monitors and len(self.images) > 0 and len(self.images) <= len(monitors):
                vx, vy, _, _ = virtual_desktop_bbox(monitors)
                for i, img in enumerate(self.images):
                    m = monitors[i]
                    AutoLayoutStrategy._apply_fit_inside(img, m["x"] - vx, m["y"] - vy, m["width"], m["height"])
                self._sync_z_indices()
                self._refresh_canvas()
                return

        AutoLayoutStrategy.apply(layout_id, self.target_w, self.target_h, self.images)
        self._sync_z_indices()
        self._refresh_canvas()
        
    def cmd_remove_img(self): 
        if self.active_idx is not None: 
            del self.images[self.active_idx]
            self._sync_z_indices()
            self.active_idx = None
            self._save_state("Del")
            self._refresh_library_panel()
            self._refresh_canvas()

    def cmd_layer_backward(self):
        if self.active_idx is None or self.active_idx <= 0:
            return
        idx = self.active_idx
        self.images[idx - 1], self.images[idx] = self.images[idx], self.images[idx - 1]
        self.active_idx = idx - 1
        self._sync_z_indices()
        self._save_state("LayerBack")
        self._refresh_library_panel()
        self._refresh_canvas()

    def cmd_layer_forward(self):
        if self.active_idx is None or self.active_idx >= len(self.images) - 1:
            return
        idx = self.active_idx
        self.images[idx + 1], self.images[idx] = self.images[idx], self.images[idx + 1]
        self.active_idx = idx + 1
        self._sync_z_indices()
        self._save_state("LayerFront")
        self._refresh_library_panel()
        self._refresh_canvas()
