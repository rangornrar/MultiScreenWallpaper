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
