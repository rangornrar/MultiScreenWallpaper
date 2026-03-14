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
        self._sim_images = [] # Prevent garbage collection of PhotoImages

        # Theme colors: Space Grey Hardware look
        self.colors = {
            "bg": "#0a0b0e",
            "side": "#12141a",
            "card": "#1c1f26",
            "accent": "#00d1ff",
            "accent_glow": "#003d4d",
            "text": "#ffffff",
            "text_dim": "#8e95a3",
            "btn_bg": "#1c1f26",
            "btn_active": "#2d333b",
            "success": "#2ea043",
            "border": "#2c313a"
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

    def _setup_ui(self):
        # Panneau Horizontal
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, bg="#333")
        main_pane.pack(fill=tk.BOTH, expand=True)
        
        # --- GAUCHE : Outils ---
        self.side_panel = tk.Frame(main_pane, bg=self.colors["side"], width=280)
        self.side_panel.pack_propagate(False)
        main_pane.add(self.side_panel, minsize=260)
        
        # Header Box (Card look)
        header_card = tk.Frame(self.side_panel, bg=self.colors["card"], bd=1, relief="flat")
        header_card.pack(fill=tk.X, padx=15, pady=(20, 10))
        
        self.lbl_title = tk.Label(header_card, text=tr("app_title"), font=("Segoe UI Semibold", 20), bg=self.colors["card"], fg=self.colors["text"])
        self.lbl_title.pack(pady=(15, 2))
        
        self.lbl_sub = tk.Label(header_card, text="", bg=self.colors["card"], fg=self.colors["accent"], font=("Segoe UI", 8, "bold"))
        self.lbl_sub.pack(pady=(0, 15))

        # Styling ttk
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=self.colors["card"], background=self.colors["card"], 
                        foreground="white", arrowcolor=self.colors["accent"], bordercolor=self.colors["border"])
        style.map("TCombobox", fieldbackground=[('readonly', self.colors["card"])])

        # sections
        def create_section(parent, label_key):
            f = tk.Frame(parent, bg=self.colors["side"])
            f.pack(fill=tk.X, padx=20, pady=8)
            lbl = tk.Label(f, text=tr(label_key).upper(), bg=self.colors["side"], fg=self.colors["text_dim"], font=("Segoe UI", 7, "bold"))
            lbl.pack(side=tk.TOP, anchor="w", pady=(0, 2))
            return f

        # --- LANGUE ---
        f_lang = create_section(self.side_panel, "lang_select")
        self.combo_lang = ttk.Combobox(f_lang, values=list(locales.LANGUAGES.values()), state="readonly")
        
        current_lang = locales.get_current_language()
        lang_keys = list(locales.LANGUAGES.keys())
        idx = lang_keys.index(current_lang) if current_lang in lang_keys else 0
        self.combo_lang.current(idx)
        self.combo_lang.pack(fill=tk.X)
        self.combo_lang.bind("<<ComboboxSelected>>", self.on_lang_changed)

        btn_style_ghost = {
            "font": ("Segoe UI", 9, "bold"),
            "bg": self.colors["side"],
            "fg": self.colors["text_dim"],
            "activebackground": self.colors["card"],
            "activeforeground": "white",
            "bd": 1,
            "highlightthickness": 0,
            "relief": "flat",
            "padx": 10,
            "pady": 6
        }
        
        # Boutons principaux
        self.btn_add = tk.Button(self.side_panel, text=tr("btn_add_images"), command=self.cmd_add_images, 
                                bg=self.colors["card"], fg="white", highlightthickness=1, highlightbackground=self.colors["border"],
                                font=("Segoe UI", 10, "bold"), bd=0, pady=12, activebackground=self.colors["border"])
        self.btn_add.pack(fill=tk.X, padx=15, pady=10)
        
        # Menu de disposition
        f_layout = create_section(self.side_panel, "lbl_layout")
        self._layout_ids = ["layout_mosaic", "layout_lines", "layout_grid", "layout_v_strip", "layout_h_strip", "layout_optimal"]
        self.combo_layout = ttk.Combobox(f_layout, state="readonly")
        self.combo_layout.pack(fill=tk.X)
        
        # Tool Buttons Row
        f_tools = tk.Frame(self.side_panel, bg=self.colors["side"])
        f_tools.pack(fill=tk.X, padx=15, pady=5)
        
        self.btn_auto = tk.Button(f_tools, text="Auto", command=self.cmd_autofill, **btn_style_ghost)
        self.btn_auto.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.btn_mode = tk.Button(f_tools, text="Mode", command=self.toggle_mode, **btn_style_ghost)
        self.btn_mode.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.btn_rem = tk.Button(f_tools, text="Remove", command=self.cmd_remove_img, **btn_style_ghost)
        self.btn_rem.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Checkbox
        self.chk_monitors = tk.Checkbutton(self.side_panel, text=tr("chk_show_monitors"), variable=self.show_monitors, 
                                          command=self._refresh_canvas, bg=self.colors["side"], fg=self.colors["text_dim"], 
                                          selectcolor="#000", activebackground=self.colors["side"], activeforeground="white", font=("Segoe UI", 9))
        self.chk_monitors.pack(pady=10)
        
        filler = tk.Frame(self.side_panel, bg=self.colors["side"])
        filler.pack(fill=tk.BOTH, expand=True)
        
        # Status
        self.status_var = tk.StringVar(value=tr("status_ready"))
        self.lbl_status = tk.Label(self.side_panel, textvariable=self.status_var, bg=self.colors["side"], fg="#444", font=("Segoe UI", 8))
        self.lbl_status.pack(side=tk.BOTTOM, pady=(5, 15))
        
        self.btn_kofi = tk.Button(self.side_panel, text=tr("btn_kofi"), command=self.cmd_open_kofi, bg=self.colors["side"], fg="#444", font=("Segoe UI", 8), bd=0, activebackground=self.colors["side"], activeforeground=self.colors["accent"], cursor="hand2")
        self.btn_kofi.pack(side=tk.BOTTOM, pady=(0, 5))

        self.btn_apply = tk.Button(self.side_panel, text=tr("btn_apply"), command=self.cmd_apply_wallpaper, 
                                  bg=self.colors["accent"], fg="black", font=("Segoe UI", 11, "bold"), bd=0, pady=15, activebackground="#00b8e6")
        self.btn_apply.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(20, 10))

        # --- DROITE : Previews ---
        self.preview_pane = ttk.Panedwindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(self.preview_pane, stretch="always")

        # Main Canvas (Interactive)
        self.canvas = tk.Canvas(self.preview_pane, bg="#111", highlightthickness=0, cursor="crosshair")
        self.preview_pane.add(self.canvas, weight=3) # Give more space to main canvas
        
        # Simulated Canvas (Real-world view)
        self.sim_canvas = tk.Canvas(self.preview_pane, bg="#0d1117", highlightthickness=0)
        self.preview_pane.add(self.sim_canvas, weight=1) # Smaller simulation area
        
        # Initialize text strings on UI load
        self._refresh_texts()
        self.combo_layout.current(0)

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_left_down)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_up)
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start); self.canvas.bind("<B2-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonPress-3>", self.on_pan_start); self.canvas.bind("<B3-Motion>", self.on_pan_drag)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom); self.canvas.bind("<Button-5>", self.on_zoom)
        
        self.sim_canvas.bind("<Configure>", lambda e: self._refresh_sim_view())

    def on_lang_changed(self, event):
        idx = self.combo_lang.current()
        if idx >= 0:
            lang_code = list(locales.LANGUAGES.keys())[idx]
            locales.set_language(lang_code)
            self._refresh_texts()
            
    def _refresh_texts(self):
        """Met à jour toutes les chaînes traductibles de l'interface"""
        self.lbl_title.config(text=tr("app_title"))
        self.lbl_sub.config(text=f"{self.target_w}x{self.target_h}  •  {tr('monitors_count', len(self.monitor_layout))}")
        
        idx = self.combo_layout.current()
        new_layouts = [tr(l_id) for l_id in self._layout_ids]
        self.combo_layout.config(values=new_layouts)
        if idx >= 0: self.combo_layout.current(idx)
        
        self.btn_mode.config(text=("ROGNER" if self.mode=="crop" else "DÉPLACER") if locales.get_current_language()=="fr" else ("CROP" if self.mode=="crop" else "MOVE"))
        self.btn_mode.config(fg="white" if self.mode=="move" else self.colors["accent"])
        self.status_var.set(tr("status_ready"))
        
    def toggle_mode(self):
        self.mode = "crop" if self.mode == "move" else "move"
        self._refresh_texts()
        # Non-toggle logic for colors moved to _refresh_texts or local config
        self._refresh_canvas()

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

    def cmd_open_kofi(self):
        webbrowser.open("https://ko-fi.com/rangorn")

    def _save_state(self, n):
        if self.history_idx < len(self.history)-1: self.history = self.history[:self.history_idx+1]
        self.history.append([i.clone() for i in self.images]); self.history_idx += 1
        if len(self.history)>20: self.history.pop(0); self.history_idx -= 1

    def cmd_undo(self):
        if self.history_idx>0: self.history_idx-=1; self._restore()
    def cmd_redo(self):
        if self.history_idx<len(self.history)-1: self.history_idx+=1; self._restore()
    def _restore(self): self.images=[i.clone() for i in self.history[self.history_idx]]; self.active_idx=None; self._refresh_canvas()
    
    def _sync_z_indices(self):
        """Assure que les indices Z correspondent à l'ordre de la liste pour le rendu"""
        for i, img in enumerate(self.images):
            img.z_index = i

    def screen_to_logic(self, sx, sy): return (sx-self.pan_x)/self.zoom, (sy-self.pan_y)/self.zoom
    def logic_to_screen(self, lx, ly): return (lx*self.zoom)+self.pan_x, (ly*self.zoom)+self.pan_y

    def _refresh_canvas(self):
        self._refresh_main_canvas()
        self._refresh_sim_view()

    def _refresh_main_canvas(self):
        self.canvas.delete("all")
        bx, by = self.logic_to_screen(0, 0); bw, bh = self.target_w*self.zoom, self.target_h*self.zoom
        self.canvas.create_rectangle(bx, by, bx+bw, by+bh, fill="#000", outline="#555")
        
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        for idx, img in sorted(enumerate(self.images), key=lambda x:x[1].z_index):
            sw, sh = int(img.w*self.zoom), int(img.h*self.zoom)
            sx, sy = self.logic_to_screen(img.x, img.y)
            if sx>cw or sy>ch or sx+sw<0 or sy+sh<0: continue
            tk_img = img.get_tk_image(sw, sh)
            if tk_img:
                self.canvas.create_image(sx, sy, image=tk_img, anchor="nw")
                if idx==self.active_idx:
                    self.canvas.create_rectangle(sx, sy, sx+sw, sy+sh, outline="cyan", width=2)
                    if self.mode=="crop": self._draw_handles(sx, sy, sw, sh)

        if self.show_monitors.get() and self.monitor_layout:
            vx, vy, _, _ = virtual_desktop_bbox(self.monitor_layout)
            for m in self.monitor_layout:
                mx, my = self.logic_to_screen(m["x"]-vx, m["y"]-vy)
                mw, mh = m["width"]*self.zoom, m["height"]*self.zoom
                self.canvas.create_rectangle(mx, my, mx+mw, my+mh, outline="#ff4444", dash=(4,4))
                self.canvas.create_text(mx+5, my+5, text=m.get("name",""), fill="red", anchor="nw")

    def _auto_fit(self):
        """Automatically adjusts zoom and offset to fit the virtual desktop in the canvas."""
        self.root.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 50 or ch < 50: return # Too small/not rendered yet

        vx0, vy0, vx1, vy1 = virtual_desktop_bbox(self.monitor_layout)
        vw, vh = vx1 - vx0, vy1 - vy0
        
        # Fit with 10% padding
        scale = min((cw * 0.9) / vw, (ch * 0.9) / vh)
        self.zoom = scale
        
        # Center
        self.offset_x = (cw - vw * scale) / 2 - vx0 * scale
        self.offset_y = (ch - vh * scale) / 2 - vy0 * scale
        self._refresh_canvas()

    def _refresh_sim_view(self):
        self.sim_canvas.delete("all")
        self._sim_images = [] # Clear previous slices
        if not self.monitor_layout: return
        
        cw, ch = self.sim_canvas.winfo_width(), self.sim_canvas.winfo_height()
        if cw < 10 or ch < 10: return
        
        # --- 0. Ambient Background (3D Wall) ---
        for y in range(ch):
            # Deeper gradient for 3D depth
            r = int(5 + (15-5) * y/ch)
            g = int(7 + (18-7) * y/ch)
            b = int(10 + (25-10) * y/ch)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.sim_canvas.create_line(0, y, cw, y, fill=color)
            
        desk_y = ch * 0.8
        # Desk texture (Linear gradient simulation)
        for y in range(int(desk_y), ch):
            v = (y - desk_y) / (ch - desk_y)
            # Metallic Space Grey desk
            r = int(20 + (5-20) * v)
            g = int(24 + (7-24) * v)
            b = int(30 + (10-30) * v)
            self.sim_canvas.create_line(0, y, cw, y, fill=f'#{r:02x}{g:02x}{b:02x}')
            
        # Highlight on desk edge
        self.sim_canvas.create_line(0, desk_y, cw, desk_y, fill="#3c444d", width=1)

        # Calculate bounding box of all monitors
        vx0, vy0, vx1, vy1 = virtual_desktop_bbox(self.monitor_layout)
        vw, vh = vx1 - vx0, vy1 - vy0

        # Centre horizontalement
        spacing_factor = 1.4
        vw_spaced = vw * spacing_factor
        
        padding = 60
        scale = min((cw - padding*2)/vw_spaced, (ch - padding*2 - 80)/vh)
        
        center_x = (vx0 + vx1) / 2
        
        ox = (cw - vw*scale*spacing_factor)/2 - vx0*scale*spacing_factor
        oy = (ch - vh*scale)/2 - vy0*scale - 40
        
        # --- 1. Draw Ambient Glow (Wall) ---
        for m in self.monitor_layout:
            # Perspective tilt factor: outer monitors compress horizontally
            dist_from_center = (m["x"] + m["width"]/2) - center_x
            tilt = 1.0 - (abs(dist_from_center) / vw) * 0.15 # 0-15% compression
            
            mx = m["x"] * scale * spacing_factor + ox
            mx_center = (m["x"] + m["width"]/2) * scale * spacing_factor + ox
            mw = m["width"] * scale * tilt
            mx = mx_center - mw/2 # Recenter compressed monitor
            
            my = m["y"] * scale + oy
            mh = m["height"] * scale
            
            # Wall glow (bloom effect)
            self.sim_canvas.create_oval(mx-mw*0.5, my-mh*0.5, mx+mw*1.5, my+mh*1.5, 
                                        fill=self.colors["accent_glow"], outline="", stipple="gray25")

        # --- 2. Draw 3D Reflections (Desk) ---
        for m in self.monitor_layout:
            dist_from_center = (m["x"] + m["width"]/2) - center_x
            tilt = 1.0 - (abs(dist_from_center) / vw) * 0.15
            mx_center = (m["x"] + m["width"]/2) * scale * spacing_factor + ox
            mw = m["width"] * scale * tilt
            mx = mx_center - mw/2
            my = m["y"] * scale + oy
            mh = m["height"] * scale
            
            # Reflection shadow/tint on desk
            ref_y = desk_y + 5
            ref_h = mh * 0.4
            self.sim_canvas.create_rectangle(mx, ref_y, mx+mw, ref_y+ref_h, fill="#080a0e", outline="", width=0)

        # --- 3. Draw Monitors (3D looking) ---
        for m in self.monitor_layout:
            dist_from_center = (m["x"] + m["width"]/2) - center_x
            tilt = 1.0 - (abs(dist_from_center) / vw) * 0.15
            # Skew effect simplified: outer edges slightly vertical offset
            skew = (dist_from_center / vw) * 8 # +/- 8 pixels skew
            
            mx_center = (m["x"] + m["width"]/2) * scale * spacing_factor + ox
            mw = m["width"] * scale * tilt
            mx = mx_center - mw/2
            my = m["y"] * scale + oy
            mh = m["height"] * scale
            
            # Stand (Premium Cylinder look)
            sx = mx + mw/2
            sy = my + mh
            self.sim_canvas.create_rectangle(sx-10, sy, sx+10, sy+desk_y-sy, fill="#1c1c1c", outline="#0a0a0a")
            self.sim_canvas.create_line(sx-10, sy, sx-10, sy+desk_y-sy, fill="#333")
            
            # Curved Base on desk
            self.sim_canvas.create_oval(sx-30, desk_y-5, sx+30, desk_y+5, fill="#121212", outline="#222")

            # Bezel (3D Frame)
            bz = 10
            # Bezel Polygon for perspective simulation
            pts = [mx-bz, my-bz+skew,  mx+mw+bz, my-bz-skew,  mx+mw+bz, my+mh+bz-skew,  mx, my+mh+bz+skew]
            self.sim_canvas.create_polygon(pts, fill="#16191f", outline="#2c313a", width=1)
            
            # Screen Content BG
            pts_s = [mx, my+skew,  mx+mw, my-skew,  mx+mw, my+mh-skew,  mx, my+mh+skew]
            self.sim_canvas.create_polygon(pts_s, fill="black", outline="")

            # Clip and draw images
            for img in sorted(self.images, key=lambda x: x.z_index):
                ix0, iy0 = img.x, img.y
                ix1, iy1 = img.x + img.w, img.y + img.h
                mx0, my0 = m["x"] - vx0, m["y"] - vy0
                mx1, my1 = mx0 + m["width"], my0 + m["height"]
                
                if ix0 < mx1 and ix1 > mx0 and iy0 < my1 and iy1 > my0:
                    cx0 = max(0, mx0 - ix0); cy0 = max(0, my0 - iy0)
                    cx1 = min(img.w, mx1 - ix0); cy1 = min(img.h, my1 - iy0)
                    
                    # Perspective coordinate mapping (simplified)
                    tx = mx + max(0, ix0 - mx0)*scale*tilt
                    ty = my + max(0, iy0 - my0)*scale + (max(0, ix0 - mx0)/m["width"] * skew * 2 - skew)
                    
                    tw = (cx1 - cx0)*scale*tilt
                    th = (cy1 - cy0)*scale
                    
                    tk_slice = img.get_tk_image_slice(cx0, cy0, cx1, cy1, int(tw), int(th))
                    if tk_slice:
                        self.sim_canvas.create_image(tx, ty, image=tk_slice, anchor="nw")
                        self._sim_images.append(tk_slice)

            # Bezel inner shadow/border
            self.sim_canvas.create_rectangle(mx, my, mx+mw, my+mh, outline="#444", width=1)
            
        # Label "Simulated View" with better style
        self.sim_canvas.create_text(20, 20, text=tr("lbl_simulated_view") if "lbl_simulated_view" in locales._STRINGS else "Monitor Setup Preview", fill="#888", font=("Segoe UI", 12, "bold"), anchor="nw")

    def _draw_handles(self, x, y, w, h):
        s=8; pts=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
        for px,py in pts: self.canvas.create_rectangle(px-s/2,py-s/2,px+s/2,py+s/2,fill="red",outline="white")

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
        if self.mode=="crop" and self.active_idx is not None:
            img = self.images[self.active_idx]
            sx, sy = self.logic_to_screen(img.x, img.y); sw, sh = img.w*self.zoom, img.h*self.zoom
            h = {"tl":(sx,sy),"tr":(sx+sw,sy),"br":(sx+sw,sy+sh),"bl":(sx,sy+sh)}
            for t, (hx,hy) in h.items():
                if abs(mx-hx)<10 and abs(my-hy)<10:
                    self._drag_data.update({"action":"resize_"+t, "item":self.active_idx, "slx":lx, "sly":ly}); return

        clicked = None; max_z = -1
        for i, img in enumerate(self.images):
            if img.x<=lx<=img.x+img.w and img.y<=ly<=img.y+img.h:
                if img.z_index>max_z: max_z=img.z_index; clicked=i
        self.active_idx = clicked
        if clicked is not None:
            img = self.images[clicked]
            self._drag_data.update({"action":"move", "item":clicked, "slx":lx, "sly":ly, "ox":img.x, "oy":img.y})
        else: self.on_pan_start(e)
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
        self._refresh_canvas()

    def on_left_up(self, e):
        if self._drag_data["action"] and self._drag_data["action"]!="pan": self._save_state(self._drag_data["action"])
        self._drag_data["action"]=None; self.canvas.config(cursor="crosshair")

    def cmd_add_images(self):
        p = askopenfilenames(filetypes=[(tr("filetype_images"), "*.jpg;*.png;*.webp;*.jpeg")])
        if p:
            ni = load_images_from_paths(p)
            for i,m in enumerate(ni):
                m.w, m.h = 600, int(600/m.current_aspect()); m.x, m.y = 50*i+self.pan_x, 50*i+self.pan_y
                m.z_index = len(self.images)+i
            self.images.extend(ni); self._save_state("Add"); self._refresh_canvas()
            
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
            del self.images[self.active_idx]; self.active_idx=None; self._save_state("Del"); self._refresh_canvas()