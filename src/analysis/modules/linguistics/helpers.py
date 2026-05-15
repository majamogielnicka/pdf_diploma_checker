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
from src.analysis.extraction.schema import *
from .linguistics_types import Block_context, Error_type
from collections import defaultdict
import functools
import spacy
from spellchecker import SpellChecker

morf = morfeusz2.Morfeusz()
spell = SpellChecker()
languages = [Language.ENGLISH, Language.POLISH]
language_detector = LanguageDetectorBuilder.from_languages(*languages).build()

nlp_en = spacy.load('en_core_web_lg')
nlp_pl = spacy.load('pl_core_news_lg')


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

    if block.type == "list":
        item_offset = 0
        for item in block.items:
            item_text = item.text.lower()
            search_from = 0
            for word in item.words:
                word_text = word.text.lower()
                idx = item_text.find(word_text, search_from)
                if idx == -1:
                    global_start = item_offset + word.start_char
                    global_end   = item_offset + word.end_char
                else:
                    global_start = item_offset + idx
                    global_end   = item_offset + idx + len(word.text)
                    search_from = idx + len(word.text)
                if global_start < end_offset and global_end > offset:
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
    output_path = os.path.join(os.path.dirname(__file__), name)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, ensure_ascii=False, indent=4)


def get_context(blocks):

    blocks_info = []
    for block in blocks.logical_blocks:
        if block.words[-1].page_number != 1:
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