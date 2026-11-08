# ui_automation.py
"""
Écrans (détection, taille réelle) et fond automatique : réapplication, rotation, icône de
notification. Mixin de WallpaperApp : ces méthodes utilisent l'état de l'application.
"""
import queue
import time
from tkinter import messagebox

from display_geometry import apply_layout, enrich_with_physical_size, layout_signature, save_settings
from dialogs import AutoDialog, PhysicalDialog
from image_tools import load_images_from_paths
from locales import tr
from screen_splitter import get_current_wallpapers, get_monitor_layout, set_multi_wallpaper_windows
from services import (TrayIcon, get_autostart, list_images, pick_rotation, render_and_apply,
                      set_autostart, wallpaper_change)


class AutomationMixin:
    def _load_monitors(self):
        """Détecte les écrans, lit leur taille physique et calcule la géométrie de composition."""
        monitors = enrich_with_physical_size(get_monitor_layout())
        self.monitor_layout = monitors
        self._layout_sig = layout_signature(monitors) if monitors else None
        if monitors:
            self.target_w, self.target_h = apply_layout(monitors, self.physical)
        else:
            self.target_w, self.target_h = 1920, 1080

    def _persist_settings(self):
        self.settings["physical"] = self.physical.to_dict()
        try:
            save_settings(self.settings)
        except OSError:
            pass

    def _relayout_after_geometry_change(self, old_size):
        """Garde les images à la même place relative quand la taille de la composition change."""
        ow, oh = old_size
        if (ow, oh) == (self.target_w, self.target_h) or not self.images:
            return
        fx, fy = self.target_w / ow, self.target_h / oh
        f = min(fx, fy)
        for img in self.images:
            cx, cy = (img.x + img.w / 2) * fx, (img.y + img.h / 2) * fy
            img.w, img.h = max(1, int(img.w * f)), max(1, int(img.h * f))
            img.x, img.y = cx - img.w / 2, cy - img.h / 2
        self._save_state("Geometry")

    def _on_monitors_changed(self, force=False):
        old_size, old_sig = (self.target_w, self.target_h), self._layout_sig
        self._load_monitors()
        if not force and self._layout_sig == old_sig:
            return False
        self._relayout_after_geometry_change(old_size)
        self._auto_fit()
        self._refresh_canvas()
        self.status_var.set(self._u("status_screens_changed"))
        return True

    def cmd_physical(self):
        if not self.monitor_layout:
            messagebox.showerror(tr("error_title"), tr("err_no_monitors"))
            return

        def on_apply(settings):
            self.physical = settings
            self._persist_settings()
            self._on_monitors_changed(force=True)
            if self.images:
                self.cmd_autofill()

        PhysicalDialog(self, self.monitor_layout, self.physical, on_apply)

    def _prefs(self):
        return {
            "keep_wallpaper": self.settings.get("keep_wallpaper", True),
            "tray": self.settings.get("tray", True),
            "autostart": get_autostart(),
            "rotation": self.settings.get("rotation", {}),
        }

    def cmd_auto_prefs(self):
        def on_apply(prefs):
            autostart = prefs.pop("autostart")
            self.settings.update(prefs)
            self._persist_settings()
            try:
                set_autostart(autostart)
            except OSError as e:
                messagebox.showerror(tr("error_title"), str(e))
            rot = prefs["rotation"]
            if rot["enabled"] and not list_images(rot["folder"]):
                messagebox.showwarning(tr("info_title"), self._u("msg_rotation_empty"))
            self._schedule_rotation(reset=True)
            self._ensure_tray()
            if self.tray:
                self.tray.refresh()

        AutoDialog(self, self._prefs(), on_apply)

    def _tray_texts(self):
        return {k: self._u("tray_" + k) for k in ("open", "reapply", "next", "rotation", "keep", "autostart", "quit")}

    def _tray_state(self):
        # Appelé depuis le thread de pystray : lecture seule de valeurs simples.
        return {
            "rotation": bool(self.settings.get("rotation", {}).get("enabled")),
            "keep": bool(self.settings.get("keep_wallpaper", True)),
            "autostart": self.settings.get("_autostart_cache", False),
        }

    def _ensure_tray(self):
        wanted = self.settings.get("tray", True)
        self.settings["_autostart_cache"] = get_autostart()
        if wanted and self.tray is None:
            tray = TrayIcon(self._tray_texts(), self._actions.put, self._tray_state)
            self.tray = tray if tray.start() else None
        elif not wanted and self.tray is not None:
            self.tray.stop()
            self.tray = None

    def _start_services(self, start_hidden):
        self._ensure_tray()
        self._schedule_rotation(reset=True)
        if start_hidden and self.tray is not None:
            self.root.withdraw()
        self.root.after(200, self._poll_actions)
        self.root.after(4000, self._service_tick)

    def _poll_actions(self):
        try:
            while True:
                self._handle_action(self._actions.get_nowait())
        except queue.Empty:
            pass
        self.root.after(200, self._poll_actions)

    def _handle_action(self, action):
        if action == "open":
            self.show_window()
        elif action == "reapply":
            self._reapply_saved(force=True)
        elif action == "next":
            self._rotation_tick(manual=True)
        elif action == "toggle_rotation":
            rot = self.settings.setdefault("rotation", {})
            rot["enabled"] = not rot.get("enabled", False)
            self._persist_settings()
            self._schedule_rotation(reset=True)
        elif action == "toggle_keep":
            self.settings["keep_wallpaper"] = not self.settings.get("keep_wallpaper", True)
            self._persist_settings()
        elif action == "toggle_autostart":
            try:
                set_autostart(not get_autostart())
            except OSError:
                pass
            self.settings["_autostart_cache"] = get_autostart()
        elif action == "quit":
            self.quit_app()
            return
        if self.tray:
            self.tray.refresh()

    def _service_tick(self):
        """Toutes les 4 s : écrans branchés/débranchés ; toutes les 60 s : fond remplacé par Windows ; rotation."""
        try:
            if not self._busy:
                raw = get_monitor_layout()
                if raw and layout_signature(raw) != self._layout_sig:
                    self._on_monitors_changed()
                    if self.settings.get("keep_wallpaper", True):
                        self._reapply_saved()
                elif self.settings.get("keep_wallpaper", True) and time.time() - self._last_keep_check > 60:
                    self._last_keep_check = time.time()
                    self._check_wallpaper_kept()
                if self._next_rotation_at and time.time() >= self._next_rotation_at:
                    self._rotation_tick()
        finally:
            self.root.after(4000, self._service_tick)

    def _check_wallpaper_kept(self):
        if self.store.is_released(self.monitor_layout):
            return
        saved = self.store.load(self.monitor_layout)
        if not saved:
            return
        expected = [path for _m, path in saved]
        monitors = self.monitor_layout

        def work(_images):
            return wallpaper_change(expected, get_current_wallpapers())

        def done(change, error):
            if error is not None:
                return
            if change == "theme":
                self._reapply_saved()
            elif change == "user":
                # Fond choisi par l'utilisateur : on ne le remplace pas.
                self.store.release(monitors)

        self._run_in_background(work, done, quiet=True)

    def _reapply_saved(self, force=False):
        """Réapplique les images mémorisées pour la configuration d'écrans actuelle (sans nouveau rendu)."""
        if not force and self.store.is_released(self.monitor_layout):
            return
        saved = self.store.load(self.monitor_layout)
        if not saved:
            if force and self.images:
                self.cmd_apply_wallpaper()
            return
        bg = self.bg_color

        def work(_images):
            return set_multi_wallpaper_windows(saved, bg)

        def done(result, error):
            if error is None and result and result[2] > 0:
                self.status_var.set(self._u("status_reapplied"))

        self._run_in_background(work, done, quiet=True)

    def _schedule_rotation(self, reset=False):
        rot = self.settings.get("rotation", {})
        if not rot.get("enabled") or not rot.get("folder"):
            self._next_rotation_at = None
            return
        if reset or self._next_rotation_at is None:
            self._next_rotation_at = time.time() + 60 * max(1, int(rot.get("minutes", 60)))

    def _rotation_tick(self, manual=False):
        """Tire de nouvelles images du dossier de rotation, les dispose et les applique en arrière-plan."""
        rot = self.settings.get("rotation", {})
        files = list_images(rot.get("folder", ""))
        self._schedule_rotation(reset=True)
        if not files or not self.monitor_layout or self._busy:
            if manual and not files:
                messagebox.showwarning(tr("info_title"), self._u("msg_rotation_empty"))
            return
        chosen = pick_rotation(files, int(rot.get("count", len(self.monitor_layout))), self._last_rotation)
        self._last_rotation = chosen
        size, monitors, bg, store = (self.target_w, self.target_h), self.monitor_layout, self.bg_color, self.store
        layout_id, fill = self._layout_id(), self._fill_enabled()

        def work(_images):
            loaded = load_images_from_paths(chosen)
            if not loaded:
                return "failed", [], []
            self._apply_auto_layout(loaded, layout_id, fill)
            return render_and_apply(loaded, size, monitors, bg, store)

        def done(result, error):
            if error is None and result and result[0] in ("ok", "partial", "span"):
                self.status_var.set(self._u("status_rotation", len(chosen)))

        self._run_in_background(work, done, quiet=True)

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _on_close(self):
        # Avec l'icône de notification, fermer la fenêtre garde le fond automatique actif.
        if self.tray is not None:
            self.root.withdraw()
        else:
            self.quit_app()

    def quit_app(self):
        if self.tray is not None:
            self.tray.stop()
            self.tray = None
        self.root.destroy()
