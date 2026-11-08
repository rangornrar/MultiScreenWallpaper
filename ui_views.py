# ui_views.py
"""Dessin de la zone de composition et de l'aperçu « vue réelle » des écrans (mixin de WallpaperApp)."""
from PIL import Image, ImageTk


class ViewsMixin:
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
            for m in self.monitor_layout:
                cx, cy, cw_, ch_ = m["canvas"]
                mx, my = self.logic_to_screen(cx, cy)
                mw, mh = cw_*self.zoom, ch_*self.zoom
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

        vw, vh = self.target_w, self.target_h

        # En taille réelle, les espaces entre écrans sont déjà dans la composition.
        gap_units = 0 if self.physical.enabled else 180
        sorted_monitors = sorted(self.monitor_layout, key=lambda m: (m["canvas"][0], m["canvas"][1]))
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
            mcx, mcy, mcw, mch = m["canvas"]
            mx = (mcx + gap_offset) * scale + ox
            my = mcy * scale + oy
            mw = mcw * scale
            mh = mch * scale

            self.sim_canvas.create_rectangle(mx + 7, my + 10, mx + mw + 7, my + mh + 12, fill="#05070b", outline="", stipple="gray50")
            self.sim_canvas.create_rectangle(mx - 6, my - 6, mx + mw + 6, my + mh + 6, fill="#151920", outline="#262d37", width=1)
            self.sim_canvas.create_rectangle(mx - 2, my - 2, mx + mw + 2, my + mh + 2, fill="#1e242d", outline="#3a4554", width=1)

            sx0, sy0 = mx + 4, my + 4
            sx1, sy1 = mx + mw - 4, my + mh - 4
            self.sim_canvas.create_rectangle(sx0, sy0, sx1, sy1, fill="#030405", outline="")

            for img in sorted(self.images, key=lambda x: x.z_index):
                ix0, iy0 = img.x, img.y
                ix1, iy1 = img.x + img.w, img.y + img.h
                mx0, my0 = mcx, mcy
                mx1, my1 = mx0 + mcw, my0 + mch

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
