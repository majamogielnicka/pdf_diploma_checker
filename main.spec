# -*- mode: python ; coding: utf-8 -*-
import os
import spellchecker  

spellchecker_dir = os.path.dirname(spellchecker.__file__)
spellchecker_resources = os.path.join(spellchecker_dir, 'resources')

a = Analysis(
    ['src/app/main.py'],
    pathex=['src'],            
    binaries=[],
    datas=[
        ('src', '.'),
        (spellchecker_resources, 'spellchecker/resources') 
    ],      
    hiddenimports=[
        'PySide6.QtSvgWidgets'  
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,             
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)