# -*- mode: python ; coding: utf-8 -*-
import os

import cv2

# Modèle de détection des visages (mode « Remplir ») ; voir facefocus._cascade_path
FACE_CASCADE = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(FACE_CASCADE, "cv2/data")],
    hiddenimports=["pystray._win32"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Modules lourds d'OpenCV/NumPy inutiles ici
    excludes=["tkinter.test", "matplotlib"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# WALLCRAFT_ONEDIR=1 : dossier au lieu d'un exe unique, pour le paquet MSIX du Microsoft Store
# (démarrage plus rapide, rien à extraire dans %TEMP%, mises à jour différentielles).
ONEDIR = os.environ.get("WALLCRAFT_ONEDIR") == "1"

if ONEDIR:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='WallCraft',
        debug=False,
        strip=False,
        upx=False,
        console=False,
    )
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='WallCraft')
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='WallCraft',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,  # UPX augmente les faux positifs antivirus
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
