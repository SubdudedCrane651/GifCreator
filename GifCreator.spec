# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import copy_metadata

# --- Include metadata for moviepy + imageio ---
datas = []
datas += copy_metadata('moviepy')
datas += copy_metadata('imageio')

# --- Bundle ffmpeg.exe ---
binaries = [
    ('ffmpeg.exe', 'ffmpeg.exe')
]

block_cipher = None

a = Analysis(
    ['GifCreator.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'moviepy',
        'imageio',
        'imageio_ffmpeg',
        'numpy',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GifCreator',
    debug=False,
    strip=False,
    upx=False,
    console=False,          # GUI mode
    icon='gif_icon.ico',   # replace with your icon file
)