# dialogs.py
"""Fenêtres secondaires de WallCraft : retouches, taille réelle des écrans, variantes, fond automatique."""
import tkinter as tk
from tkinter.filedialog import askdirectory

from PIL import Image, ImageDraw, ImageTk

from display_geometry import diagonal_inches


class _Dialog:
    """Base commune : fenêtre modale légère aux couleurs de l'application."""

    def __init__(self, app, title_key):
        self.app = app
        self.colors = app.colors
        self.win = tk.Toplevel(app.root)
        self.win.title(app._u(title_key))
        self.win.configure(bg=self.colors["panel"])
        self.win.transient(app.root)
        self.win.resizable(False, False)
        self.win.after_idle(self._center)

    def _center(self):
        """Centre la fenêtre sur l'application (le gestionnaire de fenêtres la mettrait dans un coin)."""
        if not self.win.winfo_exists():
            return
        self.win.update_idletasks()
        root = self.app.root
        w, h = self.win.winfo_reqwidth(), self.win.winfo_reqheight()
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = root.winfo_rooty() + (root.winfo_height() - h) // 3
        self.win.geometry(f"+{max(0, x)}+{max(0, y)}")

    def label(self, parent, text, row, col, **kw):
        lbl = tk.Label(parent, text=text, bg=self.colors["panel"], fg=kw.pop("fg", self.colors["text"]),
                       font=kw.pop("font", ("Segoe UI", 10)), **kw)
        lbl.grid(row=row, column=col, sticky="w", padx=(16, 8), pady=4)
        return lbl

    def entry(self, parent, var, row, col, width=8):
        e = tk.Entry(parent, textvariable=var, width=width, bg=self.colors["panel_alt"], fg=self.colors["text"],
                     insertbackground=self.colors["text"], relief="flat", font=("Segoe UI", 10))
        e.grid(row=row, column=col, sticky="w", padx=(0, 8), pady=4)
        return e

    def check(self, parent, text, var, row):
        c = tk.Checkbutton(parent, text=text, variable=var, bg=self.colors["panel"], fg=self.colors["text"],
                           selectcolor=self.colors["panel_alt"], activebackground=self.colors["panel"],
                           activeforeground=self.colors["text"], font=("Segoe UI", 10), anchor="w", justify=tk.LEFT,
                           wraplength=520)
        c.grid(row=row, column=0, columnspan=6, sticky="w", padx=12, pady=4)
        return c

    def buttons(self, row, specs, columnspan=6):
        frame = tk.Frame(self.win, bg=self.colors["panel"])
        frame.grid(row=row, column=0, columnspan=columnspan, sticky="e", padx=16, pady=(10, 14))
        for text, command in specs:
            b = tk.Button(frame, text=text, command=command, font=("Segoe UI Semibold", 9), padx=14, pady=6)
            self.app._style_button(b, "outlined")
            b.pack(side=tk.LEFT, padx=(8, 0))
        return frame


class AdjustDialog(_Dialog):
    """Luminosité, contraste, saturation, flou de l'image sélectionnée (aperçu en direct)."""

    SPECS = (
        ("brightness", "adjust_brightness", 0.2, 2.0, 0.05),
        ("contrast", "adjust_contrast", 0.2, 2.0, 0.05),
        ("saturation", "adjust_saturation", 0.0, 2.0, 0.05),
        ("blur", "adjust_blur", 0.0, 20.0, 0.5),
    )
    DEFAULTS = {"brightness": 1.0, "contrast": 1.0, "saturation": 1.0, "blur": 0.0}

    def __init__(self, app, img):
        super().__init__(app, "adjust_title")
        self.img = img
        self.variables = {}
        self.pending = None
        for row, (attr, label_key, lo, hi, step) in enumerate(self.SPECS):
            self.label(self.win, app._u(label_key), row, 0)
            var = tk.DoubleVar(value=getattr(img, attr))
            self.variables[attr] = var
            tk.Scale(self.win, from_=lo, to=hi, resolution=step, orient=tk.HORIZONTAL, length=260, variable=var,
                     command=self.on_change, bg=self.colors["panel"], fg=self.colors["text"],
                     troughcolor=self.colors["panel_alt"], highlightthickness=0).grid(row=row, column=1, padx=(0, 16), pady=6)
        self.buttons(len(self.SPECS), ((app._u("adjust_reset"), self.reset), (app._u("adjust_close"), self.close)), 2)
        self.win.protocol("WM_DELETE_WINDOW", self.close)

    def apply_now(self):
        self.pending = None
        for attr, var in self.variables.items():
            setattr(self.img, attr, float(var.get()))
        self.img.apply_filters(high_quality=False)
        self.app._refresh_canvas()

    def on_change(self, _value=None):
        if self.pending is None:
            self.pending = self.app.root.after(80, self.apply_now)

    def reset(self):
        for attr, var in self.variables.items():
            var.set(self.DEFAULTS[attr])
        self.apply_now()

    def close(self):
        if self.pending is not None:
            self.app.root.after_cancel(self.pending)
            self.apply_now()
        self.app._save_state("Adjust")
        self.app._refresh_library_panel()
        self.win.destroy()


class PhysicalDialog(_Dialog):
    """Taille réelle de chaque écran, espace entre les dalles et décalage vertical."""

    def __init__(self, app, monitors, settings, on_apply):
        super().__init__(app, "physical_title")
        self.monitors, self.settings, self.on_apply = monitors, settings, on_apply
        u = app._u
        self.enabled = tk.BooleanVar(value=settings.enabled)
        self.check(self.win, u("physical_enable"), self.enabled, 0)

        self.label(self.win, u("physical_bezel"), 1, 0)
        self.bezel = tk.StringVar(value=f"{settings.bezel_mm:g}")
        self.entry(self.win, self.bezel, 1, 1)

        headers = ("physical_screen", "physical_res", "physical_width", "physical_height", "physical_offset", "physical_diag")
        for col, key in enumerate(headers):
            self.label(self.win, u(key), 2, col, fg=self.colors["text_dim"], font=("Segoe UI Semibold", 9))

        self.rows = []
        for i, m in enumerate(monitors):
            r = 3 + i
            o = settings.overrides.get(m.get("hw_id", ""), {})
            w = o.get("width_mm") or m.get("width_mm")
            h = o.get("height_mm") or m.get("height_mm")
            vars_ = {
                "width_mm": tk.StringVar(value=f"{w:.0f}" if w else ""),
                "height_mm": tk.StringVar(value=f"{h:.0f}" if h else ""),
                "offset_y_mm": tk.StringVar(value=f"{o.get('offset_y_mm', 0):g}"),
            }
            self.label(self.win, m.get("name", f"#{i + 1}").replace("\\\\.\\", ""), r, 0)
            self.label(self.win, f"{m['width']} × {m['height']}", r, 1)
            self.entry(self.win, vars_["width_mm"], r, 2)
            self.entry(self.win, vars_["height_mm"], r, 3)
            self.entry(self.win, vars_["offset_y_mm"], r, 4)
            diag = self.label(self.win, "", r, 5, fg=self.colors["text_dim"])
            for v in (vars_["width_mm"], vars_["height_mm"]):
                v.trace_add("write", lambda *_a, vs=vars_, d=diag: self._update_diag(vs, d))
            self._update_diag(vars_, diag)
            self.rows.append((m, vars_))

        hint = tk.Label(self.win, text=u("physical_hint"), bg=self.colors["panel"], fg=self.colors["text_muted"],
                        font=("Segoe UI", 9), wraplength=620, justify=tk.LEFT)
        hint.grid(row=3 + len(monitors), column=0, columnspan=6, sticky="w", padx=16, pady=(8, 0))
        self.buttons(4 + len(monitors), ((u("btn_cancel"), self.win.destroy), (u("btn_ok"), self.ok)))

    def _update_diag(self, vars_, label):
        try:
            w, h = float(vars_["width_mm"].get()), float(vars_["height_mm"].get())
            label.config(text=f'{diagonal_inches(w, h):.1f}″')
        except ValueError:
            label.config(text=self.app._u("physical_unknown"))

    @staticmethod
    def _num(text, default=None):
        try:
            value = float(str(text).replace(",", "."))
        except ValueError:
            return default
        return value

    def ok(self):
        s = self.settings
        s.enabled = bool(self.enabled.get())
        s.bezel_mm = max(0.0, min(200.0, self._num(self.bezel.get(), 0.0)))
        for m, vars_ in self.rows:
            entry = {}
            w, h = self._num(vars_["width_mm"].get()), self._num(vars_["height_mm"].get())
            # On n'enregistre une taille que si elle diffère de celle lue dans l'écran.
            if w and h and 50 <= w <= 3000 and 50 <= h <= 3000 and (
                    not m.get("width_mm") or abs(w - m["width_mm"]) > 0.5 or abs(h - m["height_mm"]) > 0.5):
                entry["width_mm"], entry["height_mm"] = w, h
            offset = self._num(vars_["offset_y_mm"].get(), 0.0)
            if offset:
                entry["offset_y_mm"] = max(-1000.0, min(1000.0, offset))
            key = m.get("hw_id", m.get("name", ""))
            if entry:
                s.overrides[key] = entry
            else:
                s.overrides.pop(key, None)
        self.win.destroy()
        self.on_apply(s)


class VariantsDialog(_Dialog):
    """Vignettes des variantes d'une disposition ; un clic applique la variante choisie."""

    THUMB_W = 300

    def __init__(self, app, placements, on_pick):
        super().__init__(app, "variants_title")
        self._photos = []
        tw, th = app.target_w, app.target_h
        scale = self.THUMB_W / tw
        size = (self.THUMB_W, max(1, int(th * scale)))
        for i, placement in enumerate(placements):
            photo = ImageTk.PhotoImage(self._render(app, placement, size, scale))
            self._photos.append(photo)
            frame = tk.Frame(self.win, bg=self.colors["panel"])
            frame.grid(row=i // 2, column=i % 2, padx=12, pady=10)
            btn = tk.Button(frame, image=photo, command=lambda p=placement: (self.win.destroy(), on_pick(p)),
                            bg=self.colors["panel_alt"], activebackground=self.colors["accent_soft"], relief="flat",
                            bd=0, cursor="hand2", highlightthickness=2, highlightbackground=self.colors["border"])
            btn.pack()
            tk.Label(frame, text=app._u("variant_n", i + 1), bg=self.colors["panel"], fg=self.colors["text_dim"],
                     font=("Segoe UI", 9)).pack(pady=(4, 0))
        self.buttons(10, ((app._u("btn_cancel"), self.win.destroy),), 2)

    @staticmethod
    def _render(app, placement, size, scale):
        canvas = Image.new("RGB", size, (8, 12, 20))
        for img, (x, y, w, h, crop, z) in sorted(zip(app.images, placement), key=lambda t: t[1][5]):
            if not w or not h:
                continue
            src = img.display_image
            sw, sh = src.size
            cl, ct, cr, cb = crop
            piece = src.crop((int(cl * sw), int(ct * sh), max(int(cl * sw) + 1, int(cr * sw)), max(int(ct * sh) + 1, int(cb * sh))))
            pw, ph = max(1, int(w * scale)), max(1, int(h * scale))
            canvas.paste(piece.convert("RGB").resize((pw, ph)), (int(x * scale), int(y * scale)))
        d = ImageDraw.Draw(canvas)
        for m in app.monitor_layout:
            cx, cy, cw, ch = m["canvas"]
            d.rectangle([cx * scale, cy * scale, (cx + cw) * scale - 1, (cy + ch) * scale - 1], outline=(158, 203, 255))
        return canvas


class AutoDialog(_Dialog):
    """Fond automatique : garder le fond, rotation d'images, démarrage, zone de notification."""

    def __init__(self, app, prefs, on_apply):
        super().__init__(app, "prefs_title")
        u = app._u
        self.on_apply = on_apply
        rot = prefs.get("rotation", {})
        self.keep = tk.BooleanVar(value=prefs.get("keep_wallpaper", True))
        self.rotation = tk.BooleanVar(value=rot.get("enabled", False))
        self.folder = tk.StringVar(value=rot.get("folder", ""))
        self.minutes = tk.StringVar(value=str(rot.get("minutes", 60)))
        self.count = tk.StringVar(value=str(rot.get("count", max(1, len(app.monitor_layout)))))
        self.autostart = tk.BooleanVar(value=prefs.get("autostart", False))
        self.tray = tk.BooleanVar(value=prefs.get("tray", True))

        self.check(self.win, u("prefs_keep"), self.keep, 0)
        self.check(self.win, u("prefs_rotation"), self.rotation, 1)
        self.label(self.win, u("prefs_folder"), 2, 0)
        self.entry(self.win, self.folder, 2, 1, width=40)
        b = tk.Button(self.win, text=u("prefs_browse"), command=self.browse, font=("Segoe UI Semibold", 9), padx=10, pady=4)
        app._style_button(b, "outlined")
        b.grid(row=2, column=2, sticky="w", padx=(0, 16))
        self.label(self.win, u("prefs_minutes"), 3, 0)
        self.entry(self.win, self.minutes, 3, 1)
        self.label(self.win, u("prefs_count"), 4, 0)
        self.entry(self.win, self.count, 4, 1)
        self.check(self.win, u("prefs_tray"), self.tray, 5)
        self.check(self.win, u("prefs_autostart"), self.autostart, 6)
        self.buttons(7, ((u("btn_cancel"), self.win.destroy), (u("btn_ok"), self.ok)), 3)

    def browse(self):
        folder = askdirectory(parent=self.win, initialdir=self.folder.get() or None)
        if folder:
            self.folder.set(folder)

    def ok(self):
        def as_int(text, default, lo, hi):
            try:
                return max(lo, min(hi, int(float(text))))
            except ValueError:
                return default
        prefs = {
            "keep_wallpaper": bool(self.keep.get()),
            "tray": bool(self.tray.get()),
            "autostart": bool(self.autostart.get()),
            "rotation": {
                "enabled": bool(self.rotation.get()),
                "folder": self.folder.get().strip(),
                "minutes": as_int(self.minutes.get(), 60, 1, 24 * 60),
                "count": as_int(self.count.get(), 3, 1, 30),
            },
        }
        self.win.destroy()
        self.on_apply(prefs)
