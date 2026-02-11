# ui.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import tempfile

from image_tools import (
    LoadedImage, load_images_from_paths, AutoLayoutStrategy,
    compose_wallpaper_contain, save_project_json, load_project_json
)
from screen_splitter import (
    get_monitor_layout, split_wallpaper_by_monitors, 
    virtual_desktop_bbox, set_multi_wallpaper_windows
)

PRESETS = {
    "1080p (1920x1080)": (1920, 1080),
    "Triple 1080p (5760x1080)": (5760, 1080),
    "Dual QHD (5120x1440)": (5120, 1440),
    "4K (3840x2160)": (3840, 2160),
}

SNAP_DIST = 25

class WallpaperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WallCraft Pro - Performance & Multi-Screen")
        
        # Démarrage centré (80% taille écran)
        self._center_window()

        self.target_w = 5760; self.target_h = 1080
        self.bg_color = (0, 0, 0)
        self.images = []; self.active_idx = None
        
        self.history = []; self.history_idx = -1
        self.zoom = 0.15; self.pan_x = 50; self.pan_y = 50
        
        self.mode = "move"
        self._drag_data = {"x": 0, "y": 0, "item": None, "action": None}
        self.monitor_layout = get_monitor_layout()
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
        # Panneau Vertical
        main_pane = tk.PanedWindow(self.root, orient=tk.VERTICAL, sashwidth=5, bg="#444")
        main_pane.pack(fill=tk.BOTH, expand=True)
        
        # --- HAUT : Outils ---
        self.top_panel = tk.Frame(main_pane, bg="#f0f0f0", height=280)
        self.top_panel.pack_propagate(False)
        main_pane.add(self.top_panel, minsize=250)
        
        # Groupe 1: Fichiers & Undo
        grp_1 = tk.LabelFrame(self.top_panel, text="Projet", padx=5, pady=5)
        grp_1.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        tk.Button(grp_1, text="+ Ajouter", command=self.cmd_add_images, bg="#dbefff", height=2).pack(fill=tk.X)
        f_io = tk.Frame(grp_1); f_io.pack(fill=tk.X, pady=5)
        tk.Button(f_io, text="Ouvrir", command=self.cmd_load_project).pack(side=tk.LEFT)
        tk.Button(f_io, text="Sauver", command=self.cmd_save_project).pack(side=tk.LEFT)
        tk.Button(grp_1, text="↶ Undo", command=self.cmd_undo).pack(fill=tk.X)
        self.btn_mode = tk.Button(grp_1, text="Mode: DÉPLACER", bg="#ccffcc", command=self.toggle_mode)
        self.btn_mode.pack(fill=tk.X, pady=5)

        # Groupe 2: Calques
        grp_2 = tk.LabelFrame(self.top_panel, text="Calques", padx=5, pady=5)
        grp_2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.layer_list = tk.Listbox(grp_2, selectmode=tk.SINGLE)
        self.layer_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.layer_list.bind("<<ListboxSelect>>", self.on_layer_select_from_list)
        f_lay = tk.Frame(grp_2); f_lay.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Button(f_lay, text="▲", command=self.cmd_z_up).pack(fill=tk.X)
        tk.Button(f_lay, text="▼", command=self.cmd_z_down).pack(fill=tk.X)
        tk.Button(f_lay, text="🗑", command=self.cmd_remove_img, fg="red").pack(fill=tk.X, pady=5)
        f_auto = tk.Frame(f_lay); f_auto.pack(side=tk.BOTTOM, fill=tk.X)
        self.combo_layout = ttk.Combobox(f_auto, values=["grid", "horizontal", "masonry", "smart_bsp", "smart_mosaic", "justified", "lapis"], state="readonly", width=8)
        self.combo_layout.current(0); self.combo_layout.pack(fill=tk.X)
        tk.Button(f_auto, text="Auto", command=self.cmd_autofill).pack(fill=tk.X)

        # Groupe 3: Retouche
        grp_3 = tk.LabelFrame(self.top_panel, text="Retouche", padx=5, pady=5)
        grp_3.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        self.sliders = {}
        for k in ["brightness", "contrast", "saturation", "blur"]:
            f = tk.Frame(grp_3); f.pack(fill=tk.X)
            tk.Label(f, text=k[0].upper(), width=2).pack(side=tk.LEFT)
            s = tk.Scale(f, from_=(0 if k!="blur" else 0), to=(2 if k!="blur" else 10), resolution=0.1, orient=tk.HORIZONTAL, length=100, showvalue=0)
            s.set(1 if k!="blur" else 0); s.pack(side=tk.RIGHT)
            s.bind("<ButtonRelease-1>", lambda e, a=k: self.on_slider_change(a))
            self.sliders[k] = s
        tk.Button(grp_3, text="Pivot 90°", command=self.cmd_rotate).pack(fill=tk.X, pady=5)

        # Groupe 4: Export
        grp_4 = tk.LabelFrame(self.top_panel, text="Export", padx=5, pady=5)
        grp_4.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.combo_presets = ttk.Combobox(grp_4, values=list(PRESETS.keys()), width=15)
        self.combo_presets.pack(fill=tk.X)
        self.combo_presets.bind("<<ComboboxSelected>>", self.on_preset_selected)
        tk.Checkbutton(grp_4, text="Voir Ecrans", variable=self.show_monitors, command=self._refresh_canvas).pack(anchor="w")
        tk.Button(grp_4, text="💾 Export", command=lambda: self.cmd_export(False)).pack(fill=tk.X)
        tk.Button(grp_4, text="✂ Split", command=lambda: self.cmd_export(True)).pack(fill=tk.X)
        tk.Button(grp_4, text="🖥️ Appliquer", command=self.cmd_apply_wallpaper, bg="#ccffcc").pack(fill=tk.X, pady=5)
        self.status_var = tk.StringVar(value="Prêt"); tk.Label(grp_4, textvariable=self.status_var).pack(side=tk.BOTTOM)

        # --- BAS : Preview ---
        self.canvas_frame = tk.Frame(main_pane, bg="#202020")
        main_pane.add(self.canvas_frame, stretch="always")
        self.canvas = tk.Canvas(self.canvas_frame, bg="#202020", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_left_down)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_up)
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start); self.canvas.bind("<B2-Motion>", self.on_pan_drag)
        self.canvas.bind("<ButtonPress-3>", self.on_pan_start); self.canvas.bind("<B3-Motion>", self.on_pan_drag)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom); self.canvas.bind("<Button-5>", self.on_zoom)

    # --- COMMANDES ---

    def cmd_apply_wallpaper(self):
        self.status_var.set("Traitement...")
        self.root.update()
        try:
            # Rendu HD
            final = compose_wallpaper_contain((self.target_w, self.target_h), self.images, self.bg_color)
            tmp = os.path.join(tempfile.gettempdir(), "wallcraft_split")
            if not os.path.exists(tmp): os.makedirs(tmp)
            
            # Split
            results = split_wallpaper_by_monitors(final, self.monitor_layout, tmp, "screen")
            if not results: return messagebox.showerror("Err", "Aucun écran détecté")

            # Apply COM
            if set_multi_wallpaper_windows(results):
                messagebox.showinfo("OK", "Wallpaper appliqué par écran !")
            else:
                messagebox.showerror("Err", "Echec API Windows (check pywin32/comtypes)")
        except Exception as e: messagebox.showerror("Err", str(e))
        finally: self.status_var.set("Prêt")

    # --- (Le reste est standard, condensé pour tenir) ---
    def _save_state(self, n):
        if self.history_idx < len(self.history)-1: self.history = self.history[:self.history_idx+1]
        self.history.append([i.clone() for i in self.images]); self.history_idx += 1
        if len(self.history)>20: self.history.pop(0); self.history_idx -= 1

    def cmd_undo(self):
        if self.history_idx>0: self.history_idx-=1; self._restore()
    def cmd_redo(self):
        if self.history_idx<len(self.history)-1: self.history_idx+=1; self._restore()
    def _restore(self): self.images=[i.clone() for i in self.history[self.history_idx]]; self.active_idx=None; self._refresh_canvas()

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
        
        self.layer_list.delete(0, tk.END)
        for i, img in enumerate(self.images):
            self.layer_list.insert(tk.END, f"{'► ' if i==self.active_idx else ''}[{img.z_index}] {os.path.basename(img.path)}")
        if self.active_idx is not None: self.layer_list.selection_set(self.active_idx)

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
            for k in self.sliders: self.sliders[k].set(getattr(img, k))
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

    def toggle_mode(self):
        self.mode = "crop" if self.mode=="move" else "move"
        self.btn_mode.config(bg="#ffcccc" if self.mode=="crop" else "#ccffcc", text=f"Mode: {self.mode.upper()}")
        self._refresh_canvas()
    def on_slider_change(self, a):
        if self.active_idx is not None:
            v = self.sliders[a].get(); img = self.images[self.active_idx]
            if getattr(img, a)!=v: setattr(img, a, v); img.apply_filters(); self._save_state(a); self._refresh_canvas()
    def cmd_add_images(self):
        p = filedialog.askopenfilenames(filetypes=[("Img", "*.jpg;*.png;*.webp")])
        if p:
            ni = load_images_from_paths(p)
            for i,m in enumerate(ni):
                m.w, m.h = 600, int(600/m.current_aspect()); m.x, m.y = 50*i+self.pan_x, 50*i+self.pan_y
                m.z_index = len(self.images)+i
            self.images.extend(ni); self._save_state("Add"); self._refresh_canvas()
    def cmd_autofill(self): AutoLayoutStrategy.apply(self.combo_layout.get(), self.target_w, self.target_h, self.images); self._save_state("Auto"); self._refresh_canvas()
    def cmd_rotate(self): 
        if self.active_idx is not None: 
            self.images[self.active_idx].rotate_cw(); i=self.images[self.active_idx]; i.w,i.h=i.h,i.w; self._save_state("Rot"); self._refresh_canvas()
    def cmd_remove_img(self): 
        if self.active_idx is not None: del self.images[self.active_idx]; self.active_idx=None; self._save_state("Del"); self._refresh_canvas()
    def cmd_z_up(self): self._chg_z(1)
    def cmd_z_down(self): self._chg_z(-1)
    def _chg_z(self,d): 
        if self.active_idx is not None: self.images[self.active_idx].z_index+=d; self.images.sort(key=lambda x:x.z_index); self._refresh_canvas()
    def on_preset_selected(self,e): s=PRESETS.get(self.combo_presets.get()); self.target_w,self.target_h=s if s else (5760,1080); self._save_state("Res"); self._refresh_canvas()
    def on_layer_select_from_list(self,e): 
        s=self.layer_list.curselection()
        if s: self.active_idx=s[0]; i=self.images[s[0]]; [self.sliders[k].set(getattr(i,k)) for k in self.sliders]; self._refresh_canvas()
    def cmd_load_project(self): 
        p=filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if p: m,i=load_project_json(p); self.images=i; self.target_w,self.target_h=m.get("target_size",(5760,1080)); self._save_state("Load"); self._refresh_canvas()
    def cmd_save_project(self):
        p=filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if p: 
            d={"meta":{"target_size":[self.target_w,self.target_h]},"images":[{"path":i.path,"x":i.x,"y":i.y,"w":i.w,"h":i.h,"angle":i.angle,"z":i.z_index,"crop":list(i.crop_box_norm),"brightness":i.brightness,"contrast":i.contrast,"saturation":i.saturation,"blur":i.blur} for i in self.images]}
            save_project_json(p,d); messagebox.showinfo("OK","Sauvegardé")
    def cmd_export(self, split):
        p=filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png")])
        if p:
            self.status_var.set("Calcul HD..."); self.root.update()
            def t():
                try:
                    f=compose_wallpaper_contain((self.target_w, self.target_h), self.images, self.bg_color)
                    if split: split_wallpaper_by_monitors(f, self.monitor_layout, os.path.dirname(p), os.path.splitext(os.path.basename(p))[0])
                    else: f.save(p)
                    self.root.after(0, lambda: messagebox.showinfo("OK","Export Fini"))
                except Exception as e: self.root.after(0, lambda: messagebox.showerror("Err",str(e)))
                self.status_var.set("Prêt")
            threading.Thread(target=t, daemon=True).start()