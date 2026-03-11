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

        self._setup_ui()
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
        self.side_panel = tk.Frame(main_pane, bg="#222", width=250)
        self.side_panel.pack_propagate(False)
        main_pane.add(self.side_panel, minsize=220)
        
        self.lbl_title = tk.Label(self.side_panel, text=tr("app_title"), font=("Segoe UI", 16, "bold"), bg="#222", fg="white")
        self.lbl_title.pack(pady=(20, 10))
        
        self.lbl_sub = tk.Label(self.side_panel, text=f"{self.target_w}x{self.target_h}\n{tr('monitors_count', len(self.monitor_layout))}", bg="#222", fg="#aaa")
        self.lbl_sub.pack(pady=(0, 20))

        # --- LANGUE ---
        f_lang = tk.Frame(self.side_panel, bg="#222")
        f_lang.pack(fill=tk.X, padx=15, pady=5)
        self.lbl_lang = tk.Label(f_lang, text=tr("lang_select"), bg="#222", fg="#aaa", font=("Segoe UI", 9))
        self.lbl_lang.pack(side=tk.TOP, anchor="w")
        self.combo_lang = ttk.Combobox(f_lang, values=list(locales.LANGUAGES.values()), state="readonly")
        
        # Determine index of current lang
        current_lang = locales.get_current_language()
        lang_keys = list(locales.LANGUAGES.keys())
        idx = lang_keys.index(current_lang) if current_lang in lang_keys else 0
        self.combo_lang.current(idx)
        self.combo_lang.pack(fill=tk.X, pady=2)
        self.combo_lang.bind("<<ComboboxSelected>>", self.on_lang_changed)

        btn_style = {"font": ("Segoe UI", 11), "bg": "#444", "fg": "white", "activebackground": "#555", "activeforeground": "white", "bd": 0, "pady": 8}
        
        # Boutons principaux
        self.btn_add = tk.Button(self.side_panel, text=tr("btn_add_images"), command=self.cmd_add_images, bg="#2980b9", fg="white", font=("Segoe UI", 11, "bold"), bd=0, pady=10)
        self.btn_add.pack(fill=tk.X, padx=15, pady=10)
        
        # Menu de disposition
        f_layout = tk.Frame(self.side_panel, bg="#222")
        f_layout.pack(fill=tk.X, padx=15, pady=5)
        self.lbl_layout = tk.Label(f_layout, text=tr("lbl_layout"), bg="#222", fg="#aaa", font=("Segoe UI", 9))
        self.lbl_layout.pack(side=tk.TOP, anchor="w")
        
        # Map internal logic identifiers independently from display string
        self._layout_ids = ["layout_mosaic", "layout_lines", "layout_grid", "layout_v_strip", "layout_h_strip", "layout_optimal"]
        self.combo_layout = ttk.Combobox(f_layout, state="readonly")
        self.combo_layout.pack(fill=tk.X, pady=2)
        
        self.btn_auto = tk.Button(self.side_panel, text=tr("btn_auto_arrange"), command=self.cmd_autofill, **btn_style)
        self.btn_auto.pack(fill=tk.X, padx=15, pady=5)
        self.btn_mode = tk.Button(self.side_panel, text=tr("btn_mode_move"), command=self.toggle_mode, **btn_style)
        self.btn_mode.pack(fill=tk.X, padx=15, pady=5)
        self.btn_rem = tk.Button(self.side_panel, text=tr("btn_remove"), command=self.cmd_remove_img, **btn_style)
        self.btn_rem.pack(fill=tk.X, padx=15, pady=5)
        
        # Checkbox "Voir Ecrans" discret
        self.chk_monitors = tk.Checkbutton(self.side_panel, text=tr("chk_show_monitors"), variable=self.show_monitors, command=self._refresh_canvas, bg="#222", fg="#aaa", selectcolor="#333", activebackground="#222", activeforeground="#ccc")
        self.chk_monitors.pack(pady=10)
        
        # Espace
        filler = tk.Frame(self.side_panel, bg="#222")
        filler.pack(fill=tk.BOTH, expand=True)
        
        # Bottom-up packing for the bottom section
        self.status_var = tk.StringVar(value=tr("status_ready"))
        self.lbl_status = tk.Label(self.side_panel, textvariable=self.status_var, bg="#222", fg="#888", font=("Segoe UI", 9))
        self.lbl_status.pack(side=tk.BOTTOM, pady=(5, 10))
        
        # Ko-fi button just above status
        self.btn_kofi = tk.Button(self.side_panel, text=tr("btn_kofi"), command=self.cmd_open_kofi, bg="#222", fg="#ee82ee", font=("Segoe UI", 10), bd=0, activebackground="#333", activeforeground="#ee82ee", cursor="hand2")
        self.btn_kofi.pack(side=tk.BOTTOM, pady=(0, 5))

        # Apply button above Ko-fi
        self.btn_apply = tk.Button(self.side_panel, text=tr("btn_apply"), command=self.cmd_apply_wallpaper, bg="#27ae60", fg="white", font=("Segoe UI", 12, "bold"), bd=0, pady=12)
        self.btn_apply.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(20, 10))

        # --- DROITE : Preview ---
        self.canvas_frame = tk.Frame(main_pane, bg="#111")
        main_pane.add(self.canvas_frame, stretch="always")
        self.canvas = tk.Canvas(self.canvas_frame, bg="#111", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
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

    def on_lang_changed(self, event):
        idx = self.combo_lang.current()
        if idx >= 0:
            lang_code = list(locales.LANGUAGES.keys())[idx]
            locales.set_language(lang_code)
            self._refresh_texts()
            
    def _refresh_texts(self):
        """Met à jour toutes les chaînes traductibles de l'interface"""
        self.lbl_title.config(text=tr("app_title"))
        self.lbl_sub.config(text=f"{self.target_w}x{self.target_h}\n{tr('monitors_count', len(self.monitor_layout))}")
        self.lbl_lang.config(text=tr("lang_select"))
        self.btn_add.config(text=tr("btn_add_images"))
        self.lbl_layout.config(text=tr("lbl_layout"))
        
        # Refresh layout box choices maintaining selection
        idx = self.combo_layout.current()
        new_layouts = [tr(l_id) for l_id in self._layout_ids]
        self.combo_layout.config(values=new_layouts)
        if idx >= 0: self.combo_layout.current(idx)
        
        self.btn_auto.config(text=tr("btn_auto_arrange"))
        self.btn_mode.config(text=tr("btn_mode_move") if self.mode == "move" else tr("btn_mode_crop"))
        self.btn_rem.config(text=tr("btn_remove"))
        self.chk_monitors.config(text=tr("chk_show_monitors"))
        self.btn_apply.config(text=tr("btn_apply"))
        self.btn_kofi.config(text=tr("btn_kofi"))
        self.status_var.set(tr("status_ready"))
        
    def toggle_mode(self):
        self.mode = "crop" if self.mode == "move" else "move"
        self.btn_mode.config(text=tr("btn_mode_move") if self.mode == "move" else tr("btn_mode_crop"))
        self.btn_mode.config(bg="#d35400" if self.mode=="crop" else "#444")
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
            messagebox.showinfo(tr("msg_optimal_warn_title"), tr("msg_optimal_warn_text"))
            
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