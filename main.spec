# -*- mode: python ; coding: utf-8 -*-
import os
import spellchecker  
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

spellchecker_dir = os.path.dirname(spellchecker.__file__)
spellchecker_resources = os.path.join(spellchecker_dir, 'resources')

spacy_datas = collect_data_files('pl_core_news_lg') + collect_data_files('en_core_web_lg')
spacy_metadata = copy_metadata('pl_core_news_lg') + copy_metadata('en_core_web_lg')

a = Analysis(
    ['src/app/main.py'],
    pathex=['src', 'src/app', 'src/common', 'src/analysis'],            
    binaries=[],
    datas=[
        ('src', 'src'),
        (spellchecker_resources, 'spellchecker/resources'),
        ('src/ui/assets', 'ui/assets'),
        ('src/ui/assets', 'src/ui/assets'),
    ] + spacy_datas + spacy_metadata,     
    hiddenimports=[
        'PySide6.QtSvgWidgets',
        'pl_core_news_lg',
        'en_core_web_lg',
        'language_tool_python',
        'morfeusz2',
        'spellchecker',
        'lingua'
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