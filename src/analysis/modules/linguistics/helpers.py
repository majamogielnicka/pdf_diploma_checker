'''
Plik zawiera funkje pomocnicze używane wielokrotnie w module lingwistycznym, zebrane w jednym miejscu.
Uruchamiane są tu modele spacy, language_tool, morfeusz, spellchecker, 
następnie tylko przekazywane do odpowiednich funkcji.
'''
import os
import dataclasses
import json
import morfeusz2
from lingua import Language, LanguageDetectorBuilder
from analysis.extraction.schema import *
from .linguistics_types import Block_context, Error_type
from collections import defaultdict
import functools
import spacy
from spacy.language import Language as Spacy_language
from spellchecker import SpellChecker
from common.path import resource_path
import sys
import re
from pathlib import Path

morf = morfeusz2.Morfeusz()
spell = SpellChecker()
spell.word_frequency.load_text_file(resource_path(os.path.join("src", "analysis", "modules", "linguistics", "word_whitelist.txt")))
languages = [Language.ENGLISH, Language.POLISH]
language_detector = LanguageDetectorBuilder.from_languages(*languages).build()

@Spacy_language.component("fix_sentence_limits")
def fix_sentence_limits(doc):
    for i, token in enumerate(doc[1:], start=1):
        if not token.is_sent_start:
            continue
        prev = doc[i - 1]
        if token != doc[-1]:
            if prev.text in (',', ':', ';'):
                token.is_sent_start = False
            elif token.text in (',', ':', ';'):
                token.is_sent_start = False
            elif token.text[0].islower():
                token.is_sent_start = False
            #spacy rozpoznanie skrótów np. itd.
            elif prev.morph.get("Abbr") == ["Yes"]:
                token.is_sent_start = False
            elif i>=2 and doc[i - 2].morph.get("Abbr") and not token.is_title:
                token.is_sent_start = False
            elif prev.text == "." and i >= 2 and not token.is_title:
                token.is_sent_start = False

    return doc

def get_nlp(model_name):
    """Bezpieczne ładowanie dowolnego modelu spaCy w .exe i kodzie źródłowym"""
    if getattr(sys, 'frozen', False):
        base_path = Path(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))).resolve()
        
        model_path = base_path / "_internal" / model_name
        if not model_path.exists():
            model_path = base_path / model_name

        if model_path.exists():
            config_path = model_path / "config.cfg"
            if not config_path.exists():
                subdirs = [d for d in model_path.iterdir() if d.is_dir()]
                for subdir in subdirs:
                    if (subdir / "config.cfg").exists():
                        model_path = subdir
                        break
            
            print(f"[SPA CY] Ładowanie modelu z absolutnej ścieżki: {model_path.resolve()}")
            return spacy.load(model_path.resolve())
            
    return spacy.load(model_name)

nlp_pl = get_nlp("pl_core_news_lg")
nlp_pl.add_pipe("sentencizer", before="parser")
nlp_pl.add_pipe("fix_sentence_limits", after="sentencizer")
nlp_en = get_nlp("en_core_web_lg")
nlp_en.add_pipe("sentencizer", before="parser")
nlp_en.add_pipe("fix_sentence_limits", after="sentencizer")

@functools.cache
def lemmatization(word_base, text_language):
    word = word_base.lower()
    if text_language == "pl":
        nlp = nlp_pl
    else:
        nlp = nlp_en
    nlp_word = nlp(word)
    lemma = word
    for token in nlp_word:
        lemma = token.lemma_
    is_found = True
    if lemma == word:
        is_found = False
    return lemma, is_found

def language(text):
    detected = language_detector.detect_language_of(text)
    if detected == Language.POLISH:
        return 'pl'
    else:
        return 'en'

def get_match_info(block, offset, length):

    end_offset = offset + length
    word_idxs = []
    start_page = None
    end_page = None
    lines = defaultdict(list)
    if isinstance(block, ListBlock):
        item_offset = 0
        for item in block.items:
            if not item.text:
                continue
            item_end = item_offset + len(item.text)
            if item_offset >= end_offset:
                break
            if item_end > offset:
                local_start = max(0, offset - item_offset)
                local_end = min(len(item.text), end_offset - item_offset)
                item_text = item.text.lower()
                search_from = 0
                for word in item.words:
                    word_text = word.text.lower()
                    idx = item_text.find(word_text, search_from)
                    if idx == -1:
                        word_start = word.start_char
                        word_end = word.end_char
                    else:
                        word_start = idx
                        word_end = idx + len(word.text)
                        search_from = idx + len(word.text)
                    if word_start < local_end and word_end > local_start:
                        word_idxs.append(word.word_index)
                        lines[(word.page_number, word.line)].append(word)
                        if start_page is None:
                            start_page = word.page_number
                        end_page = word.page_number
            item_offset += len(item.text) + 1

    else:
        for word in block.words:
            if word.start_char < end_offset and word.end_char > offset:
                word_idxs.append(word.word_index)
                lines[(word.page_number, word.line)].append(word)
                if start_page is None:
                    start_page = word.page_number
                end_page = word.page_number

    error_coordinate = []
    for (page, line), words in sorted(lines.items()):
        error_coordinate.append({
            "page": page,
            "coordinates": [
                min(w.bbox[0] for w in words),
                min(w.bbox[1] for w in words),
                max(w.bbox[2] for w in words),
                max(w.bbox[3] for w in words),
            ]
        })
    if not error_coordinate:
        error_coordinate = [{"page": -1, "coordinates": [0, 0, 0, 0]}]

    return start_page, end_page, word_idxs, error_coordinate

def extract_errors_to_json(matches, name):

    if type(matches) is list:
        all_matches = []
        for match in matches:
            all_matches.append(dataclasses.asdict(match))
    else:
        all_matches = dataclasses.asdict(matches)
    output_path = resource_path(os.path.join("analysis", "modules", "linguistics", name))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, ensure_ascii=False, indent=4)


def get_context(blocks):

    blocks_info = []
    for block in blocks.logical_blocks:
        if not block.words:
            continue
        if block.words[-1].page_number not in {0, 1}:
            if isinstance(block, ParagraphBlock):
                contents = block.content
            elif isinstance(block, ListBlock):
                contents = " ".join(item.text for item in block.items if item.text)
            else:
                continue
            block_info = Block_context(
                block = block,
                contents = contents,
                language = language(contents),
            )
            blocks_info.append(block_info)
        
    return blocks_info

def add_match(content, block_id, page_start, page_end, word_idxs, error_coordinate, category, message):
    
    return Error_type(
                content = content,
                category = category,
                message = message,
                offset = 0,
                error_length = len(content),
                block_id = block_id,
                page_start = page_start ,
                page_end = page_end,
                word_idxs = word_idxs,
                error_coordinate= error_coordinate
            )

def extract_chapter_numbers(blocks):
    chapter_nums = []
    for block in blocks:
        if block.block.type in {'toc', 'tof', 'tot'}:
            chapter_nums.extend(re.findall(r'\b\d{1,3}\.\d{1,3}(?:\.\d{1,3})*\b', block.contents))
        if block.block.type in {'img_description', 'table_description'}:
            match = (re.search(r'\b\d{1,3}\.\d{1,3}(?:\.\d{1,3})*\b', block.contents))
            if match:
                chapter_nums.append(match.group(0))
    chapter_nums = set(chapter_nums)
    return chapter_nums