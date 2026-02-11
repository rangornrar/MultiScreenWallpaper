# main.py
import tkinter as tk
import ctypes # <--- Ajout
from ui import WallpaperApp

def main():
    # <--- AJOUTER CE BLOC POUR LA NETTETÉ ---
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    # ----------------------------------------

    root = tk.Tk()
    # (Le reste ne change pas)
    app = WallpaperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()