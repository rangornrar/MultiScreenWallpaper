# ui.py
import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename, askdirectory
import tkinter.ttk as ttk
import glob
import os
import threading
import time
import webbrowser
from PIL import ImageTk, Image

from image_tools import (
    load_images_from_paths, AutoLayoutStrategy, compose_wallpaper_contain,
    image_to_project_entry, save_project_json, load_project_json,
)
from screen_splitter import (
    get_monitor_layout, split_wallpaper_by_monitors,
    virtual_desktop_bbox, set_multi_wallpaper_windows, set_wallpaper_span,
)
import locales
from locales import tr

SNAP_DIST = 25
MIN_CROP = 0.05


def wallpaper_output_dir():
    """
    Dossier durable pour les fonds appliqués (%LOCALAPPDATA%\\WallCraft\\wallpapers).
    Windows relit ces fichiers : un dossier temporaire nettoyé ferait disparaître le fond.
    """
    base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")
    path = os.path.join(base, "WallCraft", "wallpapers")
    os.makedirs(path, exist_ok=True)
    return path


def _format_errors(errors, limit=8):
    lines = [f"• {e}" if isinstance(e, str) else f"• {os.path.basename(str(e[0]))} : {e[1]}" for e in errors[:limit]]
    if len(errors) > limit:
        lines.append(f"• … (+{len(errors) - limit})")
    return "\n".join(lines)

UI_TEXT = {
    "library_title": {"en": "Imported images", "fr": "Images importées", "es": "Imágenes importadas", "de": "Importierte Bilder"},
    "library_empty": {
        "en": "Add images to start composing a wallpaper.",
        "fr": "Ajoutez des images pour commencer une composition.",
        "es": "Añade imágenes para empezar una composición.",
        "de": "Füge Bilder hinzu, um die Komposition zu starten.",
    },
    "library_count": {"en": "{} image(s)", "fr": "{} image(s)", "es": "{} imagen(es)", "de": "{} Bild(er)"},
    "project_actions": {"en": "Project", "fr": "Projet", "es": "Proyecto", "de": "Projekt"},
    "edit_mode": {"en": "Edit mode", "fr": "Mode édition", "es": "Modo de edición", "de": "Bearbeitungsmodus"},
    "btn_new_project": {"en": "New project", "fr": "Nouveau projet", "es": "Nuevo proyecto", "de": "Neues Projekt"},
    "stage_title": {"en": "Composition stage", "fr": "Zone de composition", "es": "Zona de composición", "de": "Kompositionsfläche"},
    "stage_subtitle": {
        "en": "Move, scale, crop and arrange images inside the virtual desktop.",
        "fr": "Déplacez, redimensionnez, rognez et organisez les images dans le bureau virtuel.",
        "es": "Mueve, escala, recorta y organiza las imágenes dentro del escritorio virtual.",
        "de": "Bilder im virtuellen Desktop bewegen, skalieren, zuschneiden und anordnen.",
    },
    "output_title": {"en": "Output preview", "fr": "Aperçu de sortie", "es": "Vista de salida", "de": "Ausgabevorschau"},
    "output_subtitle": {
        "en": "Live monitor result based on your current layout.",
        "fr": "Résultat sur les écrans en direct, selon votre disposition actuelle.",
        "es": "Resultado en los monitores según la disposición actual.",
        "de": "Live-Ergebnis auf den Monitoren basierend auf dem aktuellen Layout.",
    },
    "position": {"en": "Position", "fr": "Position", "es": "Posición", "de": "Position"},
    "crop": {"en": "Visible area", "fr": "Zone visible", "es": "Zona visible", "de": "Sichtbarer Bereich"},
    "mode_move": {"en": "Move", "fr": "Déplacer", "es": "Mover", "de": "Bewegen"},
    "mode_scale": {"en": "Scale", "fr": "Redimensionner", "es": "Escalar", "de": "Skalieren"},
    "mode_crop": {"en": "Crop", "fr": "Rogner", "es": "Recortar", "de": "Zuschneiden"},
    "btn_layer_back": {"en": "Back", "fr": "Arrière", "es": "Atrás", "de": "Zurück"},
    "btn_layer_front": {"en": "Forward", "fr": "Avant", "es": "Adelante", "de": "Nach vorn"},
    "btn_rotate": {"en": "Rotate 90°", "fr": "Pivoter 90°", "es": "Girar 90°", "de": "90° drehen"},
    "btn_adjust": {"en": "Adjust…", "fr": "Retouches…", "es": "Ajustes…", "de": "Anpassen…"},
    "images_count": {"en": "{} loaded image(s)", "fr": "{} image(s) chargée(s)", "es": "{} imagen(es) cargada(s)", "de": "{} Bild(er) geladen"},
    "library_selected": {"en": "Selected", "fr": "Sélectionnée", "es": "Seleccionada", "de": "Ausgewählt"},
    "library_ready": {"en": "Ready", "fr": "Prête", "es": "Lista", "de": "Bereit"},
    "canvas_empty": {
        "en": "Add images, choose a layout, then start composing.",
        "fr": "Ajoutez des images, choisissez une disposition, puis composez.",
        "es": "Añade imágenes, elige una disposición y empieza a componer.",
        "de": "Bilder hinzufügen, Layout wählen und dann komponieren.",
    },
    "selection_empty": {"en": "No selection", "fr": "Aucune sélection", "es": "Sin selección", "de": "Keine Auswahl"},
    "selection_hint": {
        "en": "Select an image, then move, scale or crop it on the stage.",
        "fr": "Sélectionnez une image, puis déplacez-la, redimensionnez-la ou rognez-la sur la scène.",
        "es": "Selecciona una imagen y luego muévela, escálala o recórtala en la escena.",
        "de": "Bild auswählen und dann auf der Fläche bewegen, skalieren oder zuschneiden.",
    },
    "selection_summary": {
        "en": "{}  •  {} x {}  •  layer {}/{}",
        "fr": "{}  •  {} x {}  •  calque {}/{}",
        "es": "{}  •  {} x {}  •  capa {}/{}",
        "de": "{}  •  {} x {}  •  Ebene {}/{}",
    },
    "output_summary": {
        "en": "{} monitor(s)  •  {}  •  {}%",
        "fr": "{} écran(s)  •  {}  •  {}%",
        "es": "{} monitor(es)  •  {}  •  {}%",
        "de": "{} Monitor(e)  •  {}  •  {}%",
    },
    "project_reset_status": {"en": "New project ready", "fr": "Nouveau projet prêt", "es": "Nuevo proyecto listo", "de": "Neues Projekt bereit"},
    "new_project_confirm": {
        "en": "Start a new project and remove all imported images?",
        "fr": "Démarrer un nouveau projet et supprimer toutes les images importées ?",
        "es": "¿Iniciar un nuevo proyecto y eliminar todas las imágenes importadas?",
        "de": "Neues Projekt starten und alle importierten Bilder entfernen?",
    },
    # Menus
    "menu_file": {"en": "File", "fr": "Fichier", "es": "Archivo", "de": "Datei"},
    "menu_image": {"en": "Image", "fr": "Image", "es": "Imagen", "de": "Bild"},
    "menu_open": {"en": "Open project…", "fr": "Ouvrir un projet…", "es": "Abrir proyecto…", "de": "Projekt öffnen…"},
    "menu_save": {"en": "Save project…", "fr": "Enregistrer le projet…", "es": "Guardar proyecto…", "de": "Projekt speichern…"},
    "menu_export": {"en": "Export full image…", "fr": "Exporter l'image complète…", "es": "Exportar imagen completa…", "de": "Gesamtbild exportieren…"},
    "menu_split": {"en": "Export one image per screen…", "fr": "Exporter une image par écran…", "es": "Exportar una imagen por pantalla…", "de": "Ein Bild pro Bildschirm exportieren…"},
    "menu_quit": {"en": "Quit", "fr": "Quitter", "es": "Salir", "de": "Beenden"},
    "filetype_project": {"en": "WallCraft project", "fr": "Projet WallCraft", "es": "Proyecto WallCraft", "de": "WallCraft-Projekt"},
    "filetype_png": {"en": "PNG image", "fr": "Image PNG", "es": "Imagen PNG", "de": "PNG-Bild"},
    # Retouches
    "adjust_title": {"en": "Adjust image", "fr": "Retouches de l'image", "es": "Ajustes de imagen", "de": "Bild anpassen"},
    "adjust_brightness": {"en": "Brightness", "fr": "Luminosité", "es": "Brillo", "de": "Helligkeit"},
    "adjust_contrast": {"en": "Contrast", "fr": "Contraste", "es": "Contraste", "de": "Kontrast"},
    "adjust_saturation": {"en": "Saturation", "fr": "Saturation", "es": "Saturación", "de": "Sättigung"},
    "adjust_blur": {"en": "Blur", "fr": "Flou", "es": "Desenfoque", "de": "Unschärfe"},
    "adjust_reset": {"en": "Reset", "fr": "Réinitialiser", "es": "Restablecer", "de": "Zurücksetzen"},
    "adjust_close": {"en": "Close", "fr": "Fermer", "es": "Cerrar", "de": "Schließen"},
    # Messages
    "msg_saved": {"en": "Project saved: {}", "fr": "Projet enregistré : {}", "es": "Proyecto guardado: {}", "de": "Projekt gespeichert: {}"},
    "msg_exported": {"en": "Exported: {}", "fr": "Exporté : {}", "es": "Exportado: {}", "de": "Exportiert: {}"},
    "msg_split_done": {"en": "{} image(s) written to {}", "fr": "{} image(s) écrite(s) dans {}", "es": "{} imagen(es) escrita(s) en {}", "de": "{} Bild(er) gespeichert in {}"},
    "msg_load_errors": {
        "en": "Some images could not be loaded:\n\n{}",
        "fr": "Certaines images n'ont pas pu être chargées :\n\n{}",
        "es": "Algunas imágenes no se pudieron cargar:\n\n{}",
        "de": "Einige Bilder konnten nicht geladen werden:\n\n{}",
    },
    "msg_apply_partial": {
        "en": "The wallpaper was applied with warnings:\n\n{}",
        "fr": "Le fond d'écran a été appliqué avec des avertissements :\n\n{}",
        "es": "El fondo se aplicó con advertencias:\n\n{}",
        "de": "Das Hintergrundbild wurde mit Warnungen angewendet:\n\n{}",
    },
    "msg_span_fallback": {
        "en": "Per-screen mode failed:\n\n{}\n\nThe image was applied in Windows \"Span\" mode instead.",
        "fr": "Le mode par écran a échoué :\n\n{}\n\nL'image a été appliquée en mode « Étendre » de Windows à la place.",
        "es": "El modo por pantalla falló:\n\n{}\n\nLa imagen se aplicó en el modo «Extender» de Windows.",
        "de": "Der Modus pro Bildschirm ist fehlgeschlagen:\n\n{}\n\nDas Bild wurde stattdessen im Windows-Modus „Strecken“ angewendet.",
    },
    "msg_no_images": {
        "en": "Add at least one image first.",
        "fr": "Ajoutez d'abord au moins une image.",
        "es": "Añade primero al menos una imagen.",
        "de": "Füge zuerst mindestens ein Bild hinzu.",
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
        self._sim_after_id = None
        self._sim_backdrop = None
        self._sim_backdrop_key = None
        self._library_thumbs = []
        self._busy = False
        self._adjust_window = None

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
        self.root.bind("<Control-o>", lambda e: self.cmd_open_project())
        self.root.bind("<Control-s>", lambda e: self.cmd_save_project())
        self.root.bind("<Control-e>", lambda e: self.cmd_export_image())
        self.root.bind("<Control-r>", lambda e: self.cmd_rotate())
        self.root.bind("<Delete>", self._on_delete_key)

    def _on_delete_key(self, event):
        # Ne pas supprimer une image pendant la saisie dans un champ
        if isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Scale)):
            return
        self.cmd_remove_img()

    def _build_menu(self):
        menubar = tk.Menu(self.root, tearoff=False)
        self.menu_file = tk.Menu(menubar, tearoff=False)
        self.menu_image = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(menu=self.menu_file, label="")
        menubar.add_cascade(menu=self.menu_image, label="")
        self.menubar = menubar
        self.root.config(menu=menubar)

    def _refresh_menu(self):
        self.menubar.entryconfigure(0, label=self._u("menu_file"))
        self.menubar.entryconfigure(1, label=self._u("menu_image"))
        f = self.menu_file
        f.delete(0, tk.END)
        f.add_command(label=self._u("btn_new_project"), command=self.cmd_new_project)
        f.add_command(label=self._u("menu_open"), accelerator="Ctrl+O", command=self.cmd_open_project)
        f.add_command(label=self._u("menu_save"), accelerator="Ctrl+S", command=self.cmd_save_project)
        f.add_separator()
        f.add_command(label=tr("btn_add_images").lstrip("+ "), command=self.cmd_add_images)
        f.add_separator()
        f.add_command(label=self._u("menu_export"), accelerator="Ctrl+E", command=self.cmd_export_image)
        f.add_command(label=self._u("menu_split"), command=self.cmd_export_split)
        f.add_command(label=tr("btn_apply"), command=self.cmd_apply_wallpaper)
        f.add_separator()
        f.add_command(label=self._u("menu_quit"), command=self.root.destroy)
        m = self.menu_image
        m.delete(0, tk.END)
        m.add_command(label=self._u("btn_rotate"), accelerator="Ctrl+R", command=self.cmd_rotate)
        m.add_command(label=self._u("btn_adjust"), command=self.cmd_adjust)
        m.add_separator()
        m.add_command(label=self._u("btn_layer_front"), command=self.cmd_layer_forward)
        m.add_command(label=self._u("btn_layer_back"), command=self.cmd_layer_backward)
        m.add_command(label=tr("btn_remove"), accelerator="Suppr" if locales.get_current_language() == "fr" else "Del", command=self.cmd_remove_img)

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
        self._build_menu()
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
            "padx": 10,
            "pady": 9,
            "cursor": "hand2",
            "disabledforeground": self.colors["text_muted"],
        }
        tonal_button = {
            "font": ("Segoe UI Semibold", 9),
            "padx": 9,
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
        self.lbl_title = tk.Label(brand, text=tr("app_title"), font=("Segoe UI Semibold", 22), bg=self.colors["surface"], fg=self.colors["text"])
        self.lbl_title.pack(anchor="w")
        self.lbl_sub = tk.Label(brand, text="", font=("Segoe UI", 9), bg=self.colors["surface"], fg=self.colors["text_dim"])
        self.lbl_sub.pack(anchor="w", pady=(5, 0))

        tag_style = {"fg": self.colors["text_muted"], "font": ("Segoe UI", 8, "bold")}

        toolbar = tk.Frame(topbar, bg=self.colors["surface"])
        toolbar.pack(fill=tk.X, padx=18, pady=(0, 16))

        lang_card = self._make_card(toolbar, "panel_alt", "border_soft")
        lang_card.pack(side=tk.LEFT, padx=(0, 8))
        lang_inner = tk.Frame(lang_card, bg=self.colors["panel_alt"])
        lang_inner.pack(padx=12, pady=10)
        self.lbl_lang_tag = tk.Label(lang_inner, bg=self.colors["panel_alt"], **tag_style)
        self.lbl_lang_tag.pack(anchor="w")
        self.combo_lang = ttk.Combobox(lang_inner, values=list(locales.LANGUAGES.values()), state="readonly", width=10, style="WallCraft.TCombobox")
        current_lang = locales.get_current_language()
        lang_keys = list(locales.LANGUAGES.keys())
        idx = lang_keys.index(current_lang) if current_lang in lang_keys else 0
        self.combo_lang.current(idx)
        self.combo_lang.pack(fill=tk.X, pady=(6, 0))
        self.combo_lang.bind("<<ComboboxSelected>>", self.on_lang_changed)

        project_group = self._make_card(toolbar, "panel_alt", "border_soft")
        project_group.pack(side=tk.LEFT, padx=(0, 8))
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
        layout_group.pack(side=tk.LEFT, padx=(0, 8))
        layout_inner = tk.Frame(layout_group, bg=self.colors["panel_alt"])
        layout_inner.pack(padx=12, pady=10)
        self.lbl_layout_tag = tk.Label(layout_inner, bg=self.colors["panel_alt"], **tag_style)
        self.lbl_layout_tag.pack(anchor="w")
        self.combo_layout = ttk.Combobox(layout_inner, state="readonly", width=20, style="WallCraft.TCombobox")
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

        self.btn_apply = tk.Button(
            header_top,
            command=self.cmd_apply_wallpaper,
            font=("Segoe UI Semibold", 10),
            padx=22,
            pady=12,
            cursor="hand2",
        )
        self.btn_apply.pack(side=tk.RIGHT, anchor="n")
        brand.pack(side=tk.LEFT, fill=tk.X, expand=True)

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
        edit_row = tk.Frame(lib_footer, bg=self.colors["panel"])
        edit_row.pack(fill=tk.X, pady=(8, 0))
        self.btn_rotate = tk.Button(edit_row, command=self.cmd_rotate, **tonal_button)
        self.btn_rotate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.btn_adjust = tk.Button(edit_row, command=self.cmd_adjust, **tonal_button)
        self.btn_adjust.pack(side=tk.LEFT, fill=tk.X, expand=True)
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
        self.lbl_stage_title = tk.Label(stage_titles, bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI Semibold", 16))
        self.lbl_stage_title.pack(anchor="w")
        self.lbl_stage_sub = tk.Label(stage_titles, bg=self.colors["panel"], fg=self.colors["text_dim"], font=("Segoe UI", 9), anchor="w", justify=tk.LEFT)
        self.lbl_stage_sub.pack(anchor="w", fill=tk.X, pady=(4, 0))
        stage_badges = tk.Frame(stage_header, bg=self.colors["panel"])
        stage_badges.pack(side=tk.RIGHT, anchor="ne")
        self.lbl_stage_meta = tk.Label(stage_badges, bg=self.colors["accent_soft"], fg=self.colors["accent_line"], font=("Segoe UI Semibold", 9), padx=12, pady=6)
        self.lbl_stage_meta.pack(anchor="e")
        self.lbl_stage_hint = tk.Label(stage_badges, bg=self.colors["panel"], fg=self.colors["text_dim"], font=("Segoe UI", 9))
        self.lbl_stage_hint.pack(anchor="e", pady=(6, 0))
        stage_titles.pack(side=tk.LEFT, fill=tk.X, expand=True)

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
        for button in (self.btn_mode_move, self.btn_mode_scale, self.btn_mode_crop, self.btn_layer_back, self.btn_layer_front,
                       self.btn_rotate, self.btn_adjust):
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
        self.btn_rotate.config(text=self._u("btn_rotate"))
        self.btn_adjust.config(text=self._u("btn_adjust"))
        self.btn_kofi.config(text=tr("btn_kofi"))
        self._refresh_menu()
        self.btn_apply.config(text=tr("btn_apply"))
        self.chk_monitors.config(text=tr("chk_show_monitors"))

        self.lbl_library_title.config(text=self._u("library_title"))
        self.lbl_stage_title.config(text=self._u("stage_title"))
        self.lbl_stage_sub.config(text=self._u("stage_subtitle"))
        self.lbl_output_title.config(text=self._u("output_title"))
        self.lbl_output_sub.config(text=self._u("output_subtitle"))

        if not self._busy:
            self.status_var.set(tr("status_ready"))
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
        self.btn_rotate.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.btn_adjust.config(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.btn_apply.config(state=tk.DISABLED if self._busy else tk.NORMAL)
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

            ow, oh = img.original_size
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
        return self._u("mode_" + self.mode)

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

    # --- Traitements longs (rendu HD) hors du thread Tk ---

    def _run_in_background(self, work, on_done):
        """Exécute `work()` dans un thread ; `on_done(résultat, exception)` revient sur le thread Tk."""
        if self._busy:
            return
        self._busy = True
        self.status_var.set(tr("status_processing"))
        self.root.config(cursor="watch")
        self._refresh_action_states()
        snapshot = [i.clone() for i in self.images]
        outcome = {}

        def runner():
            # Aucun appel Tk ici : Tkinter n'est pas sûr hors du thread principal.
            try:
                outcome["result"], outcome["error"] = work(snapshot), None
            except Exception as e:
                outcome["result"], outcome["error"] = None, e

        def poll():
            if thread.is_alive():
                self.root.after(50, poll)
                return
            self._busy = False
            self.root.config(cursor="")
            self.status_var.set(tr("status_ready"))
            self._refresh_action_states()
            on_done(outcome.get("result"), outcome.get("error"))

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()
        self.root.after(50, poll)

    def _require_images(self):
        if not self.images:
            messagebox.showinfo(tr("info_title"), self._u("msg_no_images"))
            return False
        return True

    def cmd_apply_wallpaper(self):
        if not self._require_images():
            return
        if not self.monitor_layout:
            messagebox.showerror(tr("error_title"), tr("err_no_monitors"))
            return
        size, monitors, bg = (self.target_w, self.target_h), self.monitor_layout, self.bg_color

        def work(images):
            final = compose_wallpaper_contain(size, images, bg)
            out_dir = wallpaper_output_dir()
            # Nom unique à chaque application : Windows ne garde pas en cache une ancienne version.
            stamp = time.strftime("%Y%m%d-%H%M%S")
            prefix = f"wallcraft_{stamp}"

            def cleanup_previous():
                # Après succès seulement : en cas d'échec, l'ancien fond reste intact.
                for old in glob.glob(os.path.join(out_dir, "wallcraft_*")):
                    if not os.path.basename(old).startswith(prefix):
                        try:
                            os.remove(old)
                        except OSError:
                            pass

            results = split_wallpaper_by_monitors(final, monitors, out_dir, prefix)
            if not results:
                return "no_monitors", []
            ok, errors, applied = set_multi_wallpaper_windows(results, bg)
            if ok:
                cleanup_previous()
                return "ok", []
            if applied > 0:
                # Au moins un écran a reçu son image : on signale sans basculer en panorama.
                return "partial", errors
            span_path = os.path.join(out_dir, f"wallcraft_{stamp}_span.png")
            final.save(span_path, "PNG")
            if set_wallpaper_span(span_path):
                cleanup_previous()
                return "span", errors
            return "failed", errors

        def done(result, error):
            if error is not None:
                messagebox.showerror(tr("error_title"), str(error))
                return
            status, errors = result
            if status == "ok":
                messagebox.showinfo(tr("info_title"), tr("msg_apply_ok"))
            elif status == "partial":
                messagebox.showwarning(tr("info_title"), self._u("msg_apply_partial", _format_errors(errors)))
            elif status == "span":
                messagebox.showwarning(tr("info_title"), self._u("msg_span_fallback", _format_errors(errors)))
            elif status == "no_monitors":
                messagebox.showerror(tr("error_title"), tr("err_no_monitors"))
            else:
                detail = _format_errors(errors)
                messagebox.showerror(tr("error_title"), tr("err_api_fail") + ("\n\n" + detail if detail else ""))

        self._run_in_background(work, done)

    def cmd_export_image(self):
        if self._busy or not self._require_images():
            return
        path = asksaveasfilename(defaultextension=".png", initialfile="wallcraft.png",
                                 filetypes=[(self._u("filetype_png"), "*.png")])
        if not path:
            return
        size, bg = (self.target_w, self.target_h), self.bg_color

        def work(images):
            compose_wallpaper_contain(size, images, bg).save(path, "PNG")
            return path

        def done(result, error):
            if error is not None:
                messagebox.showerror(tr("error_title"), str(error))
            else:
                self.status_var.set(self._u("msg_exported", os.path.basename(result)))

        self._run_in_background(work, done)

    def cmd_export_split(self):
        if self._busy or not self._require_images():
            return
        if not self.monitor_layout:
            messagebox.showerror(tr("error_title"), tr("err_no_monitors"))
            return
        out_dir = askdirectory()
        if not out_dir:
            return
        size, monitors, bg = (self.target_w, self.target_h), self.monitor_layout, self.bg_color

        def work(images):
            final = compose_wallpaper_contain(size, images, bg)
            return split_wallpaper_by_monitors(final, monitors, out_dir, "wallcraft")

        def done(result, error):
            if error is not None:
                messagebox.showerror(tr("error_title"), str(error))
            else:
                messagebox.showinfo(tr("info_title"), self._u("msg_split_done", len(result), out_dir))

        self._run_in_background(work, done)

    # --- Projets ---

    def cmd_save_project(self):
        if not self._require_images():
            return
        path = asksaveasfilename(defaultextension=".wallcraft.json", initialfile="projet.wallcraft.json",
                                 filetypes=[(self._u("filetype_project"), "*.json")])
        if not path:
            return
        idx = self.combo_layout.current()
        data = {
            "meta": {
                "target": [self.target_w, self.target_h],
                "layout": self._layout_ids[idx] if idx >= 0 else None,
                "monitors": self.monitor_layout,
            },
            "images": [image_to_project_entry(img) for img in self.images],
        }
        try:
            save_project_json(path, data)
            self.status_var.set(self._u("msg_saved", os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr("error_title"), str(e))

    def cmd_open_project(self):
        if self._busy:
            return
        path = askopenfilename(filetypes=[(self._u("filetype_project"), "*.json")])
        if not path:
            return
        if self.images and not messagebox.askyesno(tr("app_title"), self._u("new_project_confirm")):
            return
        errors = []
        try:
            meta, images = load_project_json(path, errors)
        except Exception as e:
            messagebox.showerror(tr("error_title"), str(e))
            return
        self.images = images
        self._sync_z_indices()
        self.active_idx = None
        layout = meta.get("layout")
        if layout in self._layout_ids:
            self.combo_layout.current(self._layout_ids.index(layout))
        self.history = []
        self.history_idx = -1
        self._save_state("Open")
        self._refresh_library_panel()
        self._refresh_canvas()
        if errors:
            messagebox.showwarning(tr("info_title"), self._u("msg_load_errors", _format_errors(errors)))

    # --- Édition de l'image sélectionnée ---

    def _selected(self):
        if self.active_idx is None or not (0 <= self.active_idx < len(self.images)):
            return None
        return self.images[self.active_idx]

    def cmd_rotate(self):
        img = self._selected()
        if img is None:
            return
        cx, cy = img.x + img.w / 2, img.y + img.h / 2
        area = max(1, img.w * img.h)
        img.crop_box_norm = (0.0, 0.0, 1.0, 1.0)  # le rognage est défini dans l'orientation précédente
        img.rotate_cw()
        ratio = img.visible_aspect()
        img.w = max(1, int(round((area * ratio) ** 0.5)))
        img.h = max(1, int(round(img.w / ratio)))
        img.x, img.y = cx - img.w / 2, cy - img.h / 2
        self._save_state("Rotate")
        self._refresh_library_panel()
        self._refresh_canvas()

    def cmd_adjust(self):
        img = self._selected()
        if img is None:
            return
        if self._adjust_window is not None and self._adjust_window.winfo_exists():
            self._adjust_window.destroy()

        win = tk.Toplevel(self.root)
        self._adjust_window = win
        win.title(self._u("adjust_title"))
        win.configure(bg=self.colors["panel"])
        win.transient(self.root)
        win.resizable(False, False)

        specs = (
            ("brightness", "adjust_brightness", 0.2, 2.0, 0.05),
            ("contrast", "adjust_contrast", 0.2, 2.0, 0.05),
            ("saturation", "adjust_saturation", 0.0, 2.0, 0.05),
            ("blur", "adjust_blur", 0.0, 20.0, 0.5),
        )
        defaults = {"brightness": 1.0, "contrast": 1.0, "saturation": 1.0, "blur": 0.0}
        variables = {}
        pending = {"id": None}

        def apply_now():
            pending["id"] = None
            for attr, var in variables.items():
                setattr(img, attr, float(var.get()))
            img.apply_filters(high_quality=False)
            self._refresh_canvas()

        def on_change(_value=None):
            if pending["id"] is None:
                pending["id"] = self.root.after(80, apply_now)

        for row, (attr, label_key, lo, hi, step) in enumerate(specs):
            tk.Label(win, text=self._u(label_key), bg=self.colors["panel"], fg=self.colors["text"],
                     font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(16, 8), pady=6)
            var = tk.DoubleVar(value=getattr(img, attr))
            variables[attr] = var
            tk.Scale(win, from_=lo, to=hi, resolution=step, orient=tk.HORIZONTAL, length=260, variable=var,
                     command=on_change, bg=self.colors["panel"], fg=self.colors["text"],
                     troughcolor=self.colors["panel_alt"], highlightthickness=0).grid(row=row, column=1, padx=(0, 16), pady=6)

        def reset():
            for attr, var in variables.items():
                var.set(defaults[attr])
            apply_now()

        def close():
            if pending["id"] is not None:
                self.root.after_cancel(pending["id"])
                apply_now()
            self._save_state("Adjust")
            self._refresh_library_panel()
            win.destroy()

        buttons = tk.Frame(win, bg=self.colors["panel"])
        buttons.grid(row=len(specs), column=0, columnspan=2, sticky="e", padx=16, pady=(6, 14))
        for text, command in ((self._u("adjust_reset"), reset), (self._u("adjust_close"), close)):
            b = tk.Button(buttons, text=text, command=command, font=("Segoe UI Semibold", 9), padx=14, pady=6)
            self._style_button(b, "outlined")
            b.pack(side=tk.LEFT, padx=(8, 0))
        win.protocol("WM_DELETE_WINDOW", close)

    def cmd_new_project(self):
        if self._busy:
            return
        if self.images and not messagebox.askyesno(tr("app_title"), self._u("new_project_confirm")):
            return
        if self._adjust_window is not None and self._adjust_window.winfo_exists():
            self._adjust_window.destroy()

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

    def _refresh_canvas(self, live=False):
        """live=True pendant un glisser : l'aperçu des écrans est recalculé au plus toutes les 60 ms."""
        self._refresh_header_summary()
        self._refresh_main_canvas()
        if live:
            if self._sim_after_id is None:
                self._sim_after_id = self.root.after(60, self._deferred_sim_refresh)
        else:
            if self._sim_after_id is not None:
                self.root.after_cancel(self._sim_after_id)
                self._sim_after_id = None
            self._refresh_sim_view()
        self._refresh_inspector_panel()

    def _deferred_sim_refresh(self):
        self._sim_after_id = None
        self._refresh_sim_view()

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
        self.sim_canvas.create_image(0, 0, image=self._sim_backdrop_image(cw, ch, desk_y), anchor="nw")

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
            
    def _sim_backdrop_image(self, cw, ch, desk_y):
        """Dégradé mur/bureau rendu une fois par taille de canevas, au lieu d'une ligne Tk par pixel."""
        key = (cw, ch)
        if self._sim_backdrop_key != key:
            column = Image.new("RGB", (1, ch))
            for y in range(ch):
                if y < desk_y:
                    mix = y / max(1, desk_y)
                    rgb = (int(8 + 10 * mix), int(14 + 14 * mix), int(28 + 20 * mix))
                else:
                    mix = (y - desk_y) / max(1, ch - desk_y)
                    rgb = (int(20 - 10 * mix), int(24 - 12 * mix), int(32 - 16 * mix))
                column.putpixel((0, y), rgb)
            self._sim_backdrop = ImageTk.PhotoImage(column.resize((cw, ch), Image.Resampling.NEAREST))
            self._sim_backdrop_key = key
        return self._sim_backdrop

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
        self.zoom = max(0.01, min(self.zoom * f, 10.0))
        self.pan_x = mx - lx*self.zoom; self.pan_y = my - ly*self.zoom
        self._refresh_canvas()

    def on_pan_start(self, e): self._drag_data.update({"action":"pan", "lx":e.x, "ly":e.y}); self.canvas.config(cursor="fleur")
    def on_pan_drag(self, e):
        self.pan_x += e.x - self._drag_data["lx"]; self.pan_y += e.y - self._drag_data["ly"]
        self._drag_data.update({"lx":e.x, "ly":e.y}); self._refresh_canvas(live=True)

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
                    drag_data.update(
                        {
                            "ox": img.x,
                            "oy": img.y,
                            "ow": img.w,
                            "oh": img.h,
                            "aspect": max(0.01, img.w / max(1, img.h)),
                            "crop0": img.crop_box_norm,
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
            # Rognage : la partie conservée reste à la même place et à la même échelle ;
            # le cadre (x, y, w, h) suit la zone visible, donc aucune déformation.
            d = self._drag_data
            l0, t0, r0, b0 = d["crop0"]
            ow, oh = max(1, d["ow"]), max(1, d["oh"])
            dfx = (lx - d["slx"]) / ow * (r0 - l0)
            dfy = (ly - d["sly"]) / oh * (b0 - t0)
            l, t, r, b = l0, t0, r0, b0
            a = d["action"]
            if a.endswith("tl"): l += dfx; t += dfy
            elif a.endswith("br"): r += dfx; b += dfy
            elif a.endswith("tr"): r += dfx; t += dfy
            elif a.endswith("bl"): l += dfx; b += dfy
            l = min(max(0.0, l), r0 - MIN_CROP if a.endswith(("tl", "bl")) else l0)
            t = min(max(0.0, t), b0 - MIN_CROP if a.endswith(("tl", "tr")) else t0)
            r = max(min(1.0, r), l0 + MIN_CROP if a.endswith(("tr", "br")) else r0)
            b = max(min(1.0, b), t0 + MIN_CROP if a.endswith(("bl", "br")) else b0)
            img.crop_box_norm = (l, t, r, b)
            img.w = max(1, int(round(ow * (r - l) / (r0 - l0))))
            img.h = max(1, int(round(oh * (b - t) / (b0 - t0))))
            img.x = d["ox"] + (l - l0) / (r0 - l0) * ow
            img.y = d["oy"] + (t - t0) / (b0 - t0) * oh
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
        self._refresh_canvas(live=True)

    def on_left_up(self, e):
        action = self._drag_data["action"]
        if action and action!="pan":
            self._save_state(action)
            if "resize" in action or "scale" in action:
                self._refresh_library_panel()
        self._drag_data["action"]=None; self.canvas.config(cursor="crosshair")
        self._refresh_canvas()

    def cmd_add_images(self):
        p = askopenfilenames(filetypes=[(tr("filetype_images"), "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.tif;*.tiff")])
        if p:
            errors = []
            ni = load_images_from_paths(p, errors)
            if errors:
                messagebox.showwarning(tr("info_title"), self._u("msg_load_errors", _format_errors(errors)))
            if not ni:
                return
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
        idx = self.combo_layout.current()
        if idx == -1 or not self.images: return
        layout_id = self._layout_ids[idx]

        # Mosaïque avec au plus une image par écran : chaque image va sur son écran
        monitors = self.monitor_layout
        if layout_id == "layout_mosaic" and monitors and len(self.images) <= len(monitors):
            vx, vy, _, _ = virtual_desktop_bbox(monitors)
            for i, img in enumerate(self.images):
                m = monitors[i]
                AutoLayoutStrategy._apply_fit_inside(img, m["x"] - vx, m["y"] - vy, m["width"], m["height"])
        else:
            AutoLayoutStrategy.apply(layout_id, self.target_w, self.target_h, self.images)

        self._sync_z_indices()
        # Sauvegarde APRÈS la mise en page : Ctrl+Z revient à l'état précédent, Ctrl+Y la refait.
        self._save_state("Auto")
        self._refresh_library_panel()
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
