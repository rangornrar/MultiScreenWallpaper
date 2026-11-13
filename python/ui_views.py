# ui_views.py
"""Dessin de la zone de composition et de l'aperçu « vue réelle » des écrans (mixin de WallpaperApp)."""
from PIL import Image, ImageDraw, ImageTk


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

        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        self._stage_slices = []
        for idx, img in sorted(enumerate(self.images), key=lambda x:x[1].z_index):
            sw, sh = int(img.w*self.zoom), int(img.h*self.zoom)
            sx, sy = self.logic_to_screen(img.x, img.y)
            if sx>cw or sy>ch or sx+sw<0 or sy+sh<0: continue
            if sw * sh <= 4 * cw * ch:
                tk_img = img.get_tk_image(sw, sh)
                ix, iy = sx, sy
            else:
                # Fort zoom : seule la partie visible est rendue (une image entière pèserait des centaines de Mo).
                vx0, vy0 = max(0, sx), max(0, sy)
                vx1, vy1 = min(cw, sx + sw), min(ch, sy + sh)
                l, t = (vx0 - sx) / self.zoom, (vy0 - sy) / self.zoom
                r, b = (vx1 - sx) / self.zoom, (vy1 - sy) / self.zoom
                tk_img = img.get_tk_image_slice(l, t, r, b, int(vx1 - vx0), int(vy1 - vy0))
                self._stage_slices.append(tk_img)
                ix, iy = vx0, vy0
            if tk_img:
                self.canvas.create_rectangle(sx + 4, sy + 6, sx + sw + 4, sy + sh + 6, fill="#04070d", outline="", stipple="gray50")
                self.canvas.create_image(ix, iy, image=tk_img, anchor="nw")
                low = self.lowres_text(img)
                if low and sw > 90 and sh > 30:
                    self._draw_chip(self.canvas, sx + 8, sy + sh - 8, "⚠ ×" + low, "#3a2a10", self.colors["warning"], anchor="sw")
                if idx==self.active_idx:
                    self.canvas.create_rectangle(sx - 3, sy - 3, sx + sw + 3, sy + sh + 3, outline=self.colors["accent_line"], width=1)
                    self.canvas.create_rectangle(sx, sy, sx+sw, sy+sh, outline=self.colors["accent"], width=2)
                    if self.mode in ("crop", "scale"):
                        self._draw_handles(sx, sy, sw, sh)

        if self.show_monitors.get() and self.monitor_layout:
            self._dim_outside_screens(bx, by)
            for m in self.monitor_layout:
                cx, cy, cw_, ch_ = m["canvas"]
                mx, my = self.logic_to_screen(cx, cy)
                mw, mh = cw_*self.zoom, ch_*self.zoom
                self.canvas.create_rectangle(mx, my, mx+mw, my+mh, outline=self.colors["monitor"], dash=(6, 4), width=2)
                self._draw_chip(self.canvas, mx + 8, my + 8, self.monitor_label(m), "#0e2236", self.colors["monitor"], max_w=mw - 16)

        if not self.images:
            self.canvas.create_text(
                cw / 2,
                ch / 2,
                text=self._u("canvas_empty"),
                fill=self.colors["text_muted"],
                font=("Segoe UI", 12),
                width=max(260, cw - 160),
            )

    def _dim_outside_screens(self, bx, by):
        """
        Assombrit ce qui ne sera visible sur aucun écran (marges du bureau virtuel, espaces entre dalles).
        Calque semi-transparent rendu par Pillow : le pointillé (stipple) de Tk est laid et mal géré selon les systèmes.
        """
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        rects = [m["canvas"] for m in self.monitor_layout]
        key = (cw, ch, round(self.zoom, 6), round(self.pan_x, 1), round(self.pan_y, 1), tuple(map(tuple, rects)),
               self.target_w, self.target_h)
        if getattr(self, "_dim_key", None) != key:
            overlay = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            xs = sorted({0, self.target_w, *[r[0] for r in rects], *[r[0] + r[2] for r in rects]})
            ys = sorted({0, self.target_h, *[r[1] for r in rects], *[r[1] + r[3] for r in rects]})
            for x0, x1 in zip(xs, xs[1:]):
                for y0, y1 in zip(ys, ys[1:]):
                    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                    if any(r[0] <= cx <= r[0] + r[2] and r[1] <= cy <= r[1] + r[3] for r in rects):
                        continue
                    sx0, sy0 = self.logic_to_screen(x0, y0)
                    sx1, sy1 = self.logic_to_screen(x1, y1)
                    if sx1 - sx0 < 1 or sy1 - sy0 < 1:
                        continue  # bande de moins d'un pixel à ce zoom (ex. joint entre deux dalles)
                    draw.rectangle([sx0, sy0, sx1 - 1, sy1 - 1], fill=(4, 7, 14, 175))
            self._dim_image = ImageTk.PhotoImage(overlay)
            self._dim_key = key
        self.canvas.create_image(0, 0, image=self._dim_image, anchor="nw")

    def _draw_chip(self, canvas, x, y, text, bg, fg, anchor="nw", max_w=None):
        """Étiquette arrondie à la taille de son texte (tronquée si l'écran est trop étroit)."""
        font = ("Segoe UI", 8, "bold")
        item = canvas.create_text(0, 0, text=text, font=font, anchor="nw")
        x0, y0, x1, y1 = canvas.bbox(item)
        canvas.delete(item)
        w, h = (x1 - x0) + 12, (y1 - y0) + 6
        if max_w is not None and w > max_w:
            if max_w < 40:
                return
            while len(text) > 3 and w > max_w:
                text = text[:-2] + "…"
                item = canvas.create_text(0, 0, text=text, font=font, anchor="nw")
                x0, y0, x1, y1 = canvas.bbox(item)
                canvas.delete(item)
                w = (x1 - x0) + 12
        if anchor == "sw":
            y -= h
        canvas.create_rectangle(x, y, x + w, y + h, fill=bg, outline="")
        canvas.create_text(x + 6, y + h / 2, text=text, fill=fg, anchor="w", font=font)

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

                    # Échelle de la dalle (cadre de 4 px retiré) : l'image ne déborde pas sur le bord de l'écran.
                    kx, ky = (sx1 - sx0) / max(1, mcw), (sy1 - sy0) / max(1, mch)
                    tx = sx0 + max(0, ix0 - mx0) * kx
                    ty = sy0 + max(0, iy0 - my0) * ky
                    tw = (cx1 - cx0) * kx
                    th = (cy1 - cy0) * ky

                    tk_slice = img.get_tk_image_slice(cx0, cy0, cx1, cy1, int(tw), int(th))
                    if tk_slice:
                        self.sim_canvas.create_image(tx, ty, image=tk_slice, anchor="nw")
                        self._sim_images.append(tk_slice)

            self.sim_canvas.create_line(sx0, sy0 + 1, sx1, sy0 + 1, fill="#5f6979")
            self.sim_canvas.create_rectangle(sx0, sy0, sx1, sy1, outline="#0b0e13", width=1)

            self._draw_chip(self.sim_canvas, mx + 12, my + 12, self.monitor_label(m), "#232b36", "#cfd6e0", max_w=mw - 24)

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
