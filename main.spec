import os
import sys
import spellchecker  
# Dodano collect_dynamic_libs do importów
from PyInstaller.utils.hooks import collect_data_files, copy_metadata, collect_dynamic_libs

spellchecker_dir = os.path.dirname(spellchecker.__file__)
spellchecker_resources = os.path.join(spellchecker_dir, 'resources')

# 1. Zbierz wszystkie zasoby modeli językowych spaCy
spacy_datas = collect_data_files('pl_core_news_lg') + collect_data_files('en_core_web_lg')
spacy_metadata = copy_metadata('pl_core_news_lg') + copy_metadata('en_core_web_lg')

# 2. Automatycznie zbierz wszystkie pliki konfiguracyjne i metadane dla language_tool_python (w tym integrity.toml)
lt_datas = collect_data_files('language_tool_python')

# 3. Zbieranie dla llama_cpp
# collect_data_files dla zwykłych plików
llama_datas = collect_data_files('llama_cpp')
# collect_dynamic_libs dla bibliotek współdzielonych (.so)
llama_binaries = collect_dynamic_libs('llama_cpp')

a = Analysis(
    ['src/app/main.py'],
    pathex=['src', 'src/app', 'src/common', 'src/analysis'],            
    
    # DODANO llama_binaries do listy binaries
    binaries=[] + llama_binaries,
    
    datas=[
        ('src', 'src'),
        (spellchecker_resources, 'spellchecker/resources'),
        ('src/ui/assets', 'ui/assets'),
        ('src/ui/assets', 'src/ui/assets'),
        ('src/analysis/modules/linguistics/word_whitelist.txt', 'analysis/modules/linguistics'),
    ] + spacy_datas + spacy_metadata + lt_datas + llama_datas, # DODANO lt_datas i llama_datas na końcu tej listy
    
    hiddenimports=[
        'PySide6.QtSvgWidgets',
        'pl_core_news_lg',
        'en_core_web_lg',
        'language_tool_python',
        'morfeusz2',
        'spellchecker',
        'lingua',
        'llama_cpp' 
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