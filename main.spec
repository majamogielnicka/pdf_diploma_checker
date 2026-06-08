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
    # Dodajemy wszystkie foldery źródłowe, by moduły typu common/analysis były widoczne
    pathex=['src', 'src/app', 'src/common', 'src/analysis'],            
    binaries=[],
    datas=[
        ('src', '.'),
        (spellchecker_resources, 'spellchecker/resources'),
        ('src/analysis/modules/linguistics/word_whitelist.txt', 'src/analysis/modules/linguistics'),
    ] + spacy_datas + spacy_metadata, # Łączymy zebrane dane modeli SpaCy     
    hiddenimports=[
        'PySide6.QtSvgWidgets',
        'pl_core_news_lg',
        'en_core_web_lg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)