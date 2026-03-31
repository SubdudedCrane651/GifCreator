# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import copy_metadata

# --- Include metadata for moviepy + imageio ---
datas = []
datas += copy_metadata('moviepy')
datas += copy_metadata('imageio')

# --- Bundle ffmpeg.exe (must be in same folder as this spec) ---
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
    'imageio.plugins.freeimage',
    'imageio.plugins.pillow',
    'imageio.plugins._tifffile',
    'imageio.plugins.ffmpeg',
    'imageio_ffmpeg',
    'moviepy',
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
    icon='gif_icon.ico',   # replace with your icon
)