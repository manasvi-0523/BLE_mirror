# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for BLE Security System Kivy GUI.
Build with:  python -m PyInstaller ble_security.spec
"""

import os
try:
    from kivy_deps import sdl2, glew, angle
    kivy_dep_trees = [Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)]
except ImportError:
    kivy_dep_trees = []

block_cipher = None
BASE = os.path.abspath('.')

a = Analysis(
    ['gui_app.py'],
    pathex=[BASE],
    binaries=[],
    datas=[
        ('scanner', 'scanner'),
        ('feature_engine', 'feature_engine'),
        ('ai_model', 'ai_model'),
        ('blockchain', 'blockchain'),
        ('alerts', 'alerts'),
        ('app_icon.ico', '.'),
    ],
    hiddenimports=[
        'sklearn.ensemble._iforest',
        'sklearn.utils._typedefs',
        'sklearn.neighbors._partition_nodes',
        'sklearn.tree._utils',
        'pandas',
        'numpy',
        'bleak',
    ],
    hookspath=[],
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
    [],
    exclude_binaries=True,
    name='BLE_Security_System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    *kivy_dep_trees,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BLE_Security_System',
)
