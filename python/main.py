# main.py
import ctypes
import sys
import tkinter as tk

from ui import WallpaperApp


def enable_dpi_awareness():
    """
    Interface « system DPI aware » : nette sur l'écran principal, mise à l'échelle par
    Windows ailleurs. Les mesures d'écrans passent, elles, en Per-Monitor V2 le temps
    de l'appel (voir screen_splitter.per_monitor_dpi), pour rester justes en DPI mixtes.
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    enable_dpi_awareness()
    root = tk.Tk()
    # --tray : lancement au démarrage de Windows, directement dans la zone de notification
    WallpaperApp(root, start_hidden="--tray" in sys.argv)
    root.mainloop()


if __name__ == "__main__":
    main()
