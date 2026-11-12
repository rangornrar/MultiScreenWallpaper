# ui.py
"""Fenêtre principale de WallCraft : bibliothèque, barre d'outils, édition et commandes."""
import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askopenfilenames, asksaveasfilename, askdirectory
import tkinter.ttk as ttk
import os
import queue
import threading
import webbrowser
from PIL import ImageTk, Image

from image_tools import (
    load_images_from_paths, AutoLayoutStrategy, compose_wallpaper_contain,
    image_to_project_entry, save_project_json, load_project_json,
)
from screen_splitter import split_wallpaper_by_monitors
from display_geometry import PhysicalSettings, load_settings, monitor_labels, upscale_factor
from services import ConfigStore, render_and_apply
from dialogs import AdjustDialog, VariantsDialog
from ui_automation import AutomationMixin
from ui_views import ViewsMixin
import locales
from locales import tr
from ui_text import UI_TEXT

SNAP_DIST = 25
LOWRES_THRESHOLD = 1.3  # au-delà, l'image est visiblement floue sur l'écran
MIN_CROP = 0.05


def _format_errors(errors, limit=8):
    lines = [f"• {e}" if isinstance(e, str) else f"• {os.path.basename(str(e[0]))} : {e[1]}" for e in errors[:limit]]
    if len(errors) > limit:
        lines.append(f"• … (+{len(errors) - limit})")
    return "\n".join(lines)

class WallpaperApp(ViewsMixin, AutomationMixin):
    def __init__(self, root, start_hidden=False):
        self.root = root
        self.root.title(tr("app_title"))
        
        # Démarrage centré (80% taille écran)
        self._center_window()

        self.settings = load_settings()
        self.physical = PhysicalSettings.from_dict(self.settings.get("physical"))
        self.store = ConfigStore()
        self.monitor_layout = []
        self.target_w, self.target_h = 1920, 1080
        self._layout_sig = None
        self._load_monitors()

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
        self._actions = queue.Queue()  # actions venant de l'icône de notification (autre thread)
        self.tray = None
        self._last_rotation = []
        self._next_rotation_at = None
        self._last_keep_check = 0.0

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
            "text_muted": "#9aa9bf",  # contraste ≥ 6:1 sur tous les fonds de panneau
            "success": "#78d4a0",
            "danger": "#ff8a80",
            "warning": "#ffc46e",
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
        self.root.bind("<Control-n>", lambda e: self.cmd_new_project())
        self.root.bind("<Control-o>", lambda e: self.cmd_open_project())
        self.root.bind("<Control-s>", lambda e: self.cmd_save_project())
        self.root.bind("<Control-e>", lambda e: self.cmd_export_image())
        self.root.bind("<Control-r>", lambda e: self.cmd_rotate())
        self.root.bind("<Delete>", self._on_delete_key)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._start_services(start_hidden)

    def _on_delete_key(self, event):
        # Ne pas supprimer une image pendant la saisie dans un champ
        if isinstance(event.widget, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Scale)):
            return
        self.cmd_remove_img()

    def _build_menu(self):
        menubar = tk.Menu(self.root, tearoff=False)
        self.menu_file = tk.Menu(menubar, tearoff=False)
        self.menu_image = tk.Menu(menubar, tearoff=False)
        self.menu_screens = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(menu=self.menu_file, label="")
        menubar.add_cascade(menu=self.menu_image, label="")
        menubar.add_cascade(menu=self.menu_screens, label="")
        self.menu_lang = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(menu=self.menu_lang, label="")
        self.lang_var = tk.StringVar(value=locales.get_current_language())
        for code, name in locales.LANGUAGES.items():
            self.menu_lang.add_radiobutton(label=name, value=code, variable=self.lang_var, command=self.on_lang_changed)
        self.menubar = menubar
        self.root.config(menu=menubar)

    def _refresh_menu(self):
        self.menubar.entryconfigure(0, label=self._u("menu_file"))
        self.menubar.entryconfigure(1, label=self._u("menu_image"))
        self.menubar.entryconfigure(2, label=self._u("menu_screens"))
        self.menubar.entryconfigure(3, label=self._u("menu_language"))
        sc = self.menu_screens
        sc.delete(0, tk.END)
        sc.add_command(label=self._u("menu_physical"), command=self.cmd_physical)
        sc.add_command(label=self._u("menu_prefs"), command=self.cmd_auto_prefs)
        sc.add_separator()
        sc.add_command(label=self._u("menu_reload_screens"), command=lambda: self._on_monitors_changed(force=True))
        f = self.menu_file
        f.delete(0, tk.END)
        f.add_command(label=self._u("btn_new_project"), accelerator="Ctrl+N", command=self.cmd_new_project)
        f.add_command(label=self._u("menu_open"), accelerator="Ctrl+O", command=self.cmd_open_project)
        f.add_command(label=self._u("menu_save"), accelerator="Ctrl+S", command=self.cmd_save_project)
        f.add_separator()
        f.add_command(label=tr("btn_add_images").lstrip("+ "), command=self.cmd_add_images)
        f.add_separator()
        f.add_command(label=self._u("menu_export"), accelerator="Ctrl+E", command=self.cmd_export_image)
        f.add_command(label=self._u("menu_split"), command=self.cmd_export_split)
        f.add_command(label=tr("btn_apply"), command=self.cmd_apply_wallpaper)
        f.add_separator()
        f.add_command(label=self._u("menu_quit"), command=self.quit_app)
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

        if variant == "danger":
            self._style_danger(button)
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

    def _style_danger(self, button):
        button.config(bg=self.colors["panel"], fg=self.colors["danger"], activebackground="#3a1f26",
                      activeforeground=self.colors["danger"], highlightthickness=1, highlightbackground="#5a2f36",
                      highlightcolor="#5a2f36", bd=0, relief="flat")

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
        self.view_mode = "compose"  # "compose" (édition) ou "preview" (aperçu sur les écrans)
        self._build_menu()
        self.root.configure(bg=self.colors["bg"])
        self.root.minsize(1100, 700)

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
            padding=6,
        )
        style.map(
            "WallCraft.TCombobox",
            fieldbackground=[("readonly", self.colors["panel_alt"])],
            foreground=[("readonly", self.colors["text"])],
        )
        button_font = ("Segoe UI Semibold", 9)
        button = {"font": button_font, "padx": 12, "pady": 7, "cursor": "hand2", "disabledforeground": self.colors["text_muted"]}
        segment = {"font": button_font, "padx": 12, "pady": 5, "cursor": "hand2", "disabledforeground": self.colors["text_muted"]}
        caption = {"fg": self.colors["text_muted"], "font": ("Segoe UI", 9)}

        self._layout_ids = ["layout_mosaic", "layout_lines", "layout_grid", "layout_v_strip", "layout_h_strip", "layout_optimal"]

        shell = tk.Frame(self.root, bg=self.colors["bg"])
        shell.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 0))

        # --- Barre d'outils : une seule ligne (projet | disposition | appliquer) ---
        topbar = self._make_card(shell, "surface")
        topbar.pack(fill=tk.X, pady=(0, 10))
        bar = tk.Frame(topbar, bg=self.colors["surface"])
        bar.pack(fill=tk.X, padx=10, pady=8)
        self.toolbar = bar
        self.btn_apply = tk.Button(bar, command=self.cmd_apply_wallpaper, font=("Segoe UI Semibold", 10), padx=18, pady=7, cursor="hand2")
        self.btn_apply.pack(side=tk.RIGHT, padx=(10, 0))

        # « Nouveau projet » reste dans le menu Fichier (Ctrl+N) : la barre garde les actions fréquentes.
        self.btn_new = tk.Button(bar, command=self.cmd_new_project, **button)
        self.btn_add = tk.Button(bar, command=self.cmd_add_images, **button)
        self.btn_add.pack(side=tk.LEFT, padx=(0, 6))
        self._separator(bar)

        self.lbl_layout_tag = tk.Label(bar, bg=self.colors["surface"], **caption)
        self.lbl_layout_tag.pack(side=tk.LEFT, padx=(0, 6))
        self.combo_layout = ttk.Combobox(bar, state="readonly", width=19, style="WallCraft.TCombobox")
        self.combo_layout.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_auto = tk.Button(bar, command=self.cmd_autofill, **button)
        self.btn_auto.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_variants = tk.Button(bar, command=self.cmd_variants, **button)
        self.btn_variants.pack(side=tk.LEFT, padx=(0, 6))
        self._separator(bar)

        self.lbl_fit_tag = tk.Label(bar, bg=self.colors["surface"], **caption)
        self.lbl_fit_tag.pack(side=tk.LEFT, padx=(0, 6))
        fit_seg = self._segment_frame(bar)
        fit_seg.pack(side=tk.LEFT)
        self.btn_fit = tk.Button(fit_seg, command=lambda: self._set_fill(False), **segment)
        self.btn_fit.pack(side=tk.LEFT)
        self.btn_fill = tk.Button(fit_seg, command=lambda: self._set_fill(True), **segment)
        self.btn_fill.pack(side=tk.LEFT)
        self._fill = bool(self.settings.get("fill"))


        # --- Barre d'état (bas de fenêtre) ---
        statusbar = tk.Frame(self.root, bg=self.colors["surface"], highlightthickness=1, highlightbackground=self.colors["border_soft"])
        statusbar.pack(side=tk.BOTTOM, fill=tk.X, before=shell)
        self.lbl_status = tk.Label(statusbar, textvariable=self.status_var, bg=self.colors["surface"], fg=self.colors["accent_line"],
                                   font=("Segoe UI Semibold", 9), padx=12, pady=5)
        self.lbl_status.pack(side=tk.LEFT)
        self.btn_kofi = tk.Button(statusbar, command=self.cmd_open_kofi, bg=self.colors["surface"], fg=self.colors["text_muted"],
                                  activebackground=self.colors["surface"], activeforeground=self.colors["accent"], bd=0, relief="flat",
                                  highlightthickness=0, font=("Segoe UI", 9), cursor="hand2", padx=12)
        self.btn_kofi.pack(side=tk.RIGHT)
        self.lbl_sub = tk.Label(statusbar, bg=self.colors["surface"], fg=self.colors["text_dim"], font=("Segoe UI", 9), padx=8)
        self.lbl_sub.pack(side=tk.RIGHT)
        # Packé en dernier : c'est ce texte qui est coupé si la fenêtre est étroite, pas les infos à droite.
        self.lbl_selection = tk.Label(statusbar, bg=self.colors["surface"], fg=self.colors["text_dim"], font=("Segoe UI", 9), anchor="w")
        self.lbl_selection.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))

        content = tk.Frame(shell, bg=self.colors["bg"])
        content.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        content.grid_columnconfigure(0, weight=0, minsize=260)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=self.colors["bg"], width=260)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_propagate(False)
        center = tk.Frame(content, bg=self.colors["bg"])
        center.grid(row=0, column=1, sticky="nsew")

        # --- Bibliothèque : liste compacte ---
        library_card = self._make_card(left)
        library_card.pack(fill=tk.BOTH, expand=True)
        lib_header = tk.Frame(library_card, bg=self.colors["panel"])
        lib_header.pack(fill=tk.X, padx=14, pady=(12, 8))
        self.lbl_library_title = tk.Label(lib_header, bg=self.colors["panel"], fg=self.colors["text"], font=("Segoe UI Semibold", 12))
        self.lbl_library_title.pack(side=tk.LEFT)
        self.lbl_library_count = tk.Label(lib_header, bg=self.colors["panel"], fg=self.colors["text_dim"], font=("Segoe UI", 9))
        self.lbl_library_count.pack(side=tk.RIGHT)

        library_body = tk.Frame(library_card, bg=self.colors["panel"])
        self.library_canvas = tk.Canvas(library_body, bg=self.colors["panel"], bd=0, highlightthickness=0, yscrollincrement=18)
        library_scroll = tk.Scrollbar(library_body, orient="vertical", command=self.library_canvas.yview, bg=self.colors["panel_alt"],
                                      troughcolor=self.colors["panel_soft"], activebackground=self.colors["accent_soft"],
                                      highlightthickness=0, bd=0, relief="flat")
        self.library_canvas.configure(yscrollcommand=library_scroll.set)
        self.library_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        library_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.library_inner = tk.Frame(self.library_canvas, bg=self.colors["panel"])
        self._library_window = self.library_canvas.create_window((0, 0), window=self.library_inner, anchor="nw")
        self.library_inner.bind("<Configure>", self._on_library_inner_configure)
        self.library_canvas.bind("<Configure>", self._on_library_canvas_configure)
        for widget in (self.library_canvas, self.library_inner):
            widget.bind("<MouseWheel>", self._on_library_wheel)

        lib_footer = tk.Frame(library_card, bg=self.colors["panel"])
        # Pied packé avant la liste : quand la fenêtre est basse, c'est la liste qui rétrécit, pas les boutons.
        lib_footer.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(8, 12))
        library_body.pack(fill=tk.BOTH, expand=True, padx=(8, 4))
        layer_row = tk.Frame(lib_footer, bg=self.colors["panel"])
        layer_row.pack(fill=tk.X)
        self.btn_layer_back = tk.Button(layer_row, command=self.cmd_layer_backward, **button)
        self.btn_layer_back.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.btn_layer_front = tk.Button(layer_row, command=self.cmd_layer_forward, **button)
        self.btn_layer_front.pack(side=tk.LEFT, fill=tk.X, expand=True)
        edit_row = tk.Frame(lib_footer, bg=self.colors["panel"])
        edit_row.pack(fill=tk.X, pady=(6, 0))
        self.btn_rotate = tk.Button(edit_row, command=self.cmd_rotate, **button)
        self.btn_rotate.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.btn_adjust = tk.Button(edit_row, command=self.cmd_adjust, **button)
        self.btn_adjust.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # Action destructive : à part, en bas, et dans la couleur d'alerte.
        self.btn_rem = tk.Button(lib_footer, command=self.cmd_remove_img, **button)
        self.btn_rem.pack(fill=tk.X, pady=(14, 0))

        # --- Zone de travail unique : Composition / Aperçu sur les écrans ---
        stage_card = self._make_card(center)
        stage_card.pack(fill=tk.BOTH, expand=True)
        stage_header = tk.Frame(stage_card, bg=self.colors["panel"])
        stage_header.pack(fill=tk.X, padx=10, pady=(10, 8))

        self.stage_header = stage_header
        self.chk_monitors = tk.Checkbutton(
            stage_header, variable=self.show_monitors, command=self._refresh_canvas,
            bg=self.colors["panel"], fg=self.colors["text_dim"], activebackground=self.colors["panel"],
            activeforeground=self.colors["text"], selectcolor=self.colors["panel_alt"], highlightthickness=0,
            bd=0, font=("Segoe UI", 9), cursor="hand2",
        )
        self.chk_monitors.pack(side=tk.RIGHT)  # packé avant les outils : jamais tronqué
        view_seg = self._segment_frame(stage_header)
        view_seg.pack(side=tk.LEFT)
        self.view_seg = view_seg
        self.btn_view_compose = tk.Button(view_seg, command=lambda: self.set_view("compose"), **segment)
        self.btn_view_compose.pack(side=tk.LEFT)
        self.btn_view_preview = tk.Button(view_seg, command=lambda: self.set_view("preview"), **segment)
        self.btn_view_preview.pack(side=tk.LEFT)

        self.tools_box = tk.Frame(stage_header, bg=self.colors["panel"])
        # Pas de libellé « Outil » : les trois boutons se suffisent et la barre reste lisible en allemand à 1100 px.
        tool_seg = self._segment_frame(self.tools_box)
        tool_seg.pack(side=tk.LEFT, padx=(14, 0))
        self.btn_mode_move = tk.Button(tool_seg, command=lambda: self.set_mode("move"), **segment)
        self.btn_mode_move.pack(side=tk.LEFT)
        self.btn_mode_scale = tk.Button(tool_seg, command=lambda: self.set_mode("scale"), **segment)
        self.btn_mode_scale.pack(side=tk.LEFT)
        self.btn_mode_crop = tk.Button(tool_seg, command=lambda: self.set_mode("crop"), **segment)
        self.btn_mode_crop.pack(side=tk.LEFT)
        self.tools_box.pack(side=tk.LEFT)

        self.lbl_preview_hint = tk.Label(stage_header, bg=self.colors["panel"], fg=self.colors["text_dim"], font=("Segoe UI", 9))

        self.stage_shell = tk.Frame(stage_card, bg=self.colors["canvas_bg"])
        self.stage_shell.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.canvas = tk.Canvas(self.stage_shell, bg=self.colors["canvas_bg"], highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.sim_canvas = tk.Canvas(self.stage_shell, bg=self.colors["panel_soft"], highlightthickness=0)

        for b in (self.btn_new, self.btn_add, self.btn_auto, self.btn_variants, self.btn_layer_back, self.btn_layer_front,
                  self.btn_rotate, self.btn_adjust):
            self._style_button(b, "outlined")
        self._style_button(self.btn_rem, "danger")
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
        self.canvas.bind("<Configure>", self._on_stage_resized)
        self.sim_canvas.bind("<Configure>", lambda e: self._refresh_sim_view())

    def _update_min_width(self):
        """La fenêtre ne peut pas devenir plus étroite que la barre d'outils (dont la largeur dépend de la langue)."""
        self.root.update_idletasks()
        needed = max(self.toolbar.winfo_reqwidth() + 46, 260 + 10 + self.stage_header.winfo_reqwidth() + 56, 1100)
        self.root.minsize(needed, 700)

    def _separator(self, parent):
        tk.Frame(parent, bg=self.colors["border"], width=1, height=26).pack(side=tk.LEFT, padx=(4, 10))

    def _segment_frame(self, parent):
        return tk.Frame(parent, bg=self.colors["border"], padx=1, pady=1)

    def _style_segment(self, button, active):
        if active:
            button.config(bg=self.colors["accent"], fg=self.colors["canvas_bg"], activebackground=self.colors["accent_line"],
                          activeforeground=self.colors["canvas_bg"], relief="flat", bd=0, highlightthickness=0)
        else:
            button.config(bg=self.colors["panel_alt"], fg=self.colors["text"], activebackground=self.colors["accent_soft"],
                          activeforeground=self.colors["text"], relief="flat", bd=0, highlightthickness=0)

    def _on_stage_resized(self, _event=None):
        # La zone grandit avec la fenêtre : on recadre tant que l'utilisateur n'a pas zoomé lui-même.
        if not getattr(self, "_user_zoomed", False):
            self.root.after_idle(self._auto_fit)
        else:
            self._refresh_canvas()

    def _on_library_wheel(self, event):
        self.library_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def set_view(self, view):
        if view not in ("compose", "preview") or view == self.view_mode:
            return
        self.view_mode = view
        if view == "preview":
            self.canvas.pack_forget()
            self.sim_canvas.pack(fill=tk.BOTH, expand=True)
            self.tools_box.pack_forget()
            self.chk_monitors.pack_forget()
            self.lbl_preview_hint.pack(side=tk.LEFT, padx=(18, 0))
        else:
            self.sim_canvas.pack_forget()
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.lbl_preview_hint.pack_forget()
            self.chk_monitors.pack(side=tk.RIGHT, before=self.view_seg)
            self.tools_box.pack(side=tk.LEFT, after=self.view_seg)
        self._refresh_view_buttons()
        self._refresh_canvas()

    def _refresh_view_buttons(self):
        self._style_segment(self.btn_view_compose, self.view_mode == "compose")
        self._style_segment(self.btn_view_preview, self.view_mode == "preview")
        self._style_segment(self.btn_fit, not self._fill)
        self._style_segment(self.btn_fill, self._fill)

    def _n(self, key, n):
        """Texte accordé : _n("n_screens", 1) → « 1 écran », _n("n_screens", 3) → « 3 écrans »."""
        forms = UI_TEXT[key].get(locales.get_current_language(), UI_TEXT[key]["en"])
        return forms[0 if n == 1 else 1].format(n)

    def _decimal(self):
        return "." if locales.get_current_language() == "en" else ","

    def _monitor_label_map(self):
        """{id(moniteur): « Gauche · Philips 23″ »}, recalculé quand la langue ou les écrans changent."""
        key = (locales.get_current_language(), tuple((m.get("name"), tuple(m.get("canvas", ()))) for m in self.monitor_layout))
        if getattr(self, "_labels_key", None) != key:
            words = {k: self._u("pos_" + k) for k in ("left", "center", "right", "top", "bottom", "screen")}
            labels = monitor_labels(self.monitor_layout, words, self._decimal())
            self._labels = {id(m): label for m, label in zip(self.monitor_layout, labels)}
            self._labels_key = key
        return self._labels

    def monitor_label(self, m):
        return self._monitor_label_map().get(id(m), m.get("name", ""))

    def lowres_text(self, img):
        """« ×2,5 » si l'image est nettement agrandie, sinon None."""
        factor = upscale_factor(img)
        if factor < LOWRES_THRESHOLD:
            return None
        return f"{factor:.1f}".replace(".", self._decimal())

    def _on_library_inner_configure(self, _event=None):
        self.library_canvas.configure(scrollregion=self.library_canvas.bbox("all"))

    def _on_library_canvas_configure(self, event):
        self.library_canvas.itemconfigure(self._library_window, width=event.width)

    def _select_image(self, idx):
        if 0 <= idx < len(self.images):
            self.active_idx = idx
            self._refresh_library_panel()
            self._refresh_canvas()

    def on_lang_changed(self, _event=None):
        locales.set_language(self.lang_var.get())
        self._refresh_texts()
        self._refresh_canvas()
            
    def _refresh_texts(self):
        self.root.title(tr("app_title"))
        self.lbl_layout_tag.config(text=tr("lbl_layout"))
        self.lbl_fit_tag.config(text=self._u("lbl_fit"))

        idx = self.combo_layout.current()
        new_layouts = [tr(l_id) for l_id in self._layout_ids]
        self.combo_layout.config(values=new_layouts)
        if idx >= 0:
            self.combo_layout.current(idx)

        self.btn_new.config(text=self._u("btn_new_project"))
        self.btn_add.config(text=tr("btn_add_images"))
        self.btn_auto.config(text=tr("btn_auto_arrange"))
        self.btn_variants.config(text=self._u("btn_variants"))
        self.btn_fit.config(text=self._u("fill_fit"))
        self.btn_fill.config(text=self._u("fill_fill"))
        self.btn_rem.config(text=tr("btn_remove"))
        self.btn_layer_back.config(text=self._u("btn_layer_back"))
        self.btn_layer_front.config(text=self._u("btn_layer_front"))
        self.btn_rotate.config(text=self._u("btn_rotate"))
        self.btn_adjust.config(text=self._u("btn_adjust"))
        self.btn_kofi.config(text=tr("btn_kofi"))
        self._refresh_menu()
        self.btn_apply.config(text=tr("btn_apply"))
        self.chk_monitors.config(text=tr("chk_show_monitors"))
        self.btn_view_compose.config(text=self._u("view_compose"))
        self.btn_view_preview.config(text=self._u("view_preview"))
        self.lbl_preview_hint.config(text=self._u("preview_hint"))
        self.lbl_library_title.config(text=self._u("library_title"))

        if not self._busy:
            self.status_var.set(tr("status_ready"))
        self._update_min_width()
        self._refresh_mode_buttons()
        self._refresh_view_buttons()
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
            self._style_segment(button, self.mode == mode)

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
            text=f"{self.target_w} × {self.target_h}  •  {self._n('n_screens', screen_count)}"
                 + (f" ({self._u('physical_badge')})" if self.physical.enabled else "")
                 + f"  •  {self._n('n_images', len(self.images))}"
        )

    def _refresh_library_panel(self):
        for child in self.library_inner.winfo_children():
            child.destroy()

        self._library_thumbs = []
        self.lbl_library_count.config(text=self._n("n_images", len(self.images)))
        self._refresh_action_states()

        if not self.images:
            empty = tk.Label(self.library_inner, text=self._u("library_empty"), bg=self.colors["panel"], fg=self.colors["text_muted"],
                             font=("Segoe UI", 10), wraplength=200, justify=tk.LEFT, padx=8, pady=18)
            empty.pack(fill=tk.X, padx=4, pady=(6, 10))
            return

        thumb_w, thumb_h = 76, 48
        name_chars = 24
        # Ordre d'affichage : le calque du dessus en premier, comme dans un logiciel de dessin.
        for idx in reversed(range(len(self.images))):
            img = self.images[idx]
            active = idx == self.active_idx
            bg = self.colors["accent_soft"] if active else self.colors["panel"]
            border = self.colors["accent"] if active else self.colors["panel"]

            item = tk.Frame(self.library_inner, bg=bg, highlightthickness=1, highlightbackground=border, highlightcolor=border, bd=0)
            item.pack(fill=tk.X, padx=2, pady=(0, 4))

            thumb = self._make_contained_preview(img, thumb_w, thumb_h)
            self._library_thumbs.append(thumb)
            thumb_label = tk.Label(item, image=thumb, bg=bg, bd=0)
            thumb_label.pack(side=tk.LEFT, padx=(6, 8), pady=6)

            text = tk.Frame(item, bg=bg)
            text.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=6)
            name = os.path.basename(img.path)
            if len(name) > name_chars:
                name = name[: name_chars // 2 - 1] + "…" + name[-(name_chars // 2 - 1):]
            title = tk.Label(text, text=name, bg=bg, fg=self.colors["text"], font=("Segoe UI Semibold", 9), anchor="w")
            title.pack(fill=tk.X)
            ow, oh = img.original_size
            meta = tk.Label(text, text=f"{ow} × {oh}", bg=bg, fg=self.colors["text_dim"], font=("Segoe UI", 9), anchor="w")
            meta.pack(fill=tk.X)
            widgets = [item, thumb_label, text, title, meta]

            low = self.lowres_text(img)
            if low:
                warn = tk.Label(text, text="⚠ " + self._u("lowres_badge", low), bg=bg, fg=self.colors["warning"],
                                font=("Segoe UI Semibold", 8), anchor="w")
                warn.pack(fill=tk.X, pady=(2, 0))
                widgets.append(warn)

            for widget in widgets:
                widget.bind("<Button-1>", lambda _e, i=idx: self._select_image(i))
                widget.bind("<MouseWheel>", self._on_library_wheel)

    def _get_mode_name(self):
        return self._u("mode_" + self.mode)

    def _refresh_inspector_panel(self):
        img = self._selected()
        if img is None:
            self.lbl_selection.config(text=self._u("selection_hint") if self.images else "", fg=self.colors["text_dim"])
            return
        name = os.path.basename(img.path)
        if len(name) > 34:
            name = f"{name[:16]}…{name[-12:]}"
        parts = [
            self._u("selection_summary", name, int(img.w), int(img.h), img.z_index + 1, max(1, len(self.images))),
            f"{self._u('position')} {int(img.x)}, {int(img.y)}",
            f"{self._u('crop')} {int((img.crop_box_norm[2] - img.crop_box_norm[0]) * 100)} %",
        ]
        low = self.lowres_text(img)
        if low:
            parts.append("⚠ " + self._u("lowres_tip", low))
        self.lbl_selection.config(text="  •  ".join(parts), fg=self.colors["warning"] if low else self.colors["text_dim"])

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

    def _run_in_background(self, work, on_done, quiet=False):
        """Exécute `work()` dans un thread ; `on_done(résultat, exception)` revient sur le thread Tk."""
        if self._busy:
            return
        self._busy = True
        if not quiet:  # les tâches de fond (surveillance, rotation) ne changent pas le curseur
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
            if not quiet:
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

        store = self.store

        def work(images):
            return render_and_apply(images, size, monitors, bg, store)

        def done(result, error):
            if error is not None:
                messagebox.showerror(tr("error_title"), str(error))
                return
            status, errors, _results = result
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
                "fill": self._fill_enabled(),
                "physical": self.physical.enabled,
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
        if "fill" in meta:
            self._fill = bool(meta.get("fill"))
            self._refresh_view_buttons()
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
        if self._adjust_window is not None and self._adjust_window.win.winfo_exists():
            self._adjust_window.win.destroy()
        self._adjust_window = AdjustDialog(self, img)

    def cmd_new_project(self):
        if self._busy:
            return
        if self.images and not messagebox.askyesno(tr("app_title"), self._u("new_project_confirm")):
            return
        if self._adjust_window is not None and self._adjust_window.win.winfo_exists():
            self._adjust_window.win.destroy()

        self.images = []
        self.active_idx = None
        self.history = []
        self.history_idx = -1
        self.mode = "move"
        self._user_zoomed = False
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
        """Redessine la vue affichée (composition, ou aperçu sur les écrans limité à une fois toutes les 60 ms pendant un glisser)."""
        self._refresh_header_summary()
        if self.view_mode == "compose":
            self._refresh_main_canvas()
            self._refresh_inspector_panel()
            return
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



            

    def on_zoom(self, e):
        f = 1.1 if (e.num==4 or e.delta>0) else 0.9
        mx, my = self.canvas.canvasx(e.x), self.canvas.canvasy(e.y)
        lx, ly = self.screen_to_logic(mx, my)
        self.zoom = max(0.01, min(self.zoom * f, 10.0))
        self._user_zoomed = True
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
            
    def _layout_id(self):
        idx = self.combo_layout.current()
        return self._layout_ids[idx] if idx >= 0 else self._layout_ids[0]

    def _fill_enabled(self):
        return self._fill

    def _set_fill(self, fill):
        if fill == self._fill:
            return
        self._fill = fill
        self._refresh_view_buttons()
        self._on_fill_changed()

    def _on_fill_changed(self, _event=None):
        self.settings["fill"] = self._fill_enabled()
        self._persist_settings()
        if self.images:
            self.cmd_autofill()

    def _apply_auto_layout(self, images, layout_id, fill, variant=0):
        """Mise en page sans toucher à l'interface (utilisée aussi par la rotation automatique)."""
        monitors = self.monitor_layout
        if layout_id == "layout_mosaic" and monitors and len(images) <= len(monitors):
            # Mosaïque avec au plus une image par écran : chaque image va sur son écran
            rects = [m["canvas"] for m in sorted(monitors, key=lambda m: (m["canvas"][0], m["canvas"][1]))]
            AutoLayoutStrategy.place_on_screens(images, rects, fill=fill)
        else:
            AutoLayoutStrategy.apply(layout_id, self.target_w, self.target_h, images, fill=fill, variant=variant)

    def cmd_autofill(self):
        if not self.images: return
        self._apply_auto_layout(self.images, self._layout_id(), self._fill_enabled())
        self._sync_z_indices()
        # Sauvegarde APRÈS la mise en page : Ctrl+Z revient à l'état précédent, Ctrl+Y la refait.
        self._save_state("Auto")
        self._refresh_library_panel()
        self._refresh_canvas()

    def cmd_variants(self):
        """Calcule 4 variantes de la disposition choisie et les montre côte à côte."""
        if self._busy or not self._require_images():
            return
        layout_id, fill = self._layout_id(), self._fill_enabled()
        if layout_id == "layout_mosaic" and len(self.images) <= len(self.monitor_layout):
            layout_id = "layout_optimal"  # une image par écran n'a qu'une variante
        size = (self.target_w, self.target_h)
        self.status_var.set(self._u("variants_computing"))

        def work(images):
            return AutoLayoutStrategy.variants(layout_id, size[0], size[1], images, fill=fill)

        def done(result, error):
            if error is not None:
                messagebox.showerror(tr("error_title"), str(error))
                return
            VariantsDialog(self, result, self._apply_variant)

        self._run_in_background(work, done)

    def _apply_variant(self, placement):
        AutoLayoutStrategy.apply_placement(self.images, placement)
        self._sync_z_indices()
        self._save_state("Variant")
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
            self.status_var.set(self._u("status_removed"))

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

    # --- Écrans : détection, taille réelle ---






    # --- Fond automatique, rotation, zone de notification ---
















