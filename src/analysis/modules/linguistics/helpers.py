import os
import dataclasses
import json
import morfeusz2
from lingua import Language, LanguageDetectorBuilder
from src.analysis.extraction.schema import *
from .linguistics_types import Block_context

morf = morfeusz2.Morfeusz()
languages = [Language.ENGLISH, Language.POLISH]
language_detector = LanguageDetectorBuilder.from_languages(*languages).build()

def language(text):
    '''
    Detects language of a block for further text analysis.
    Args:
        text (str): string of text to be analysed.
        
    Returns:
        str: 'pl' for Polish and 'en' for English

    '''
    detected = language_detector.detect_language_of(text)
    if detected == Language.POLISH:
        return 'pl'
    else:
        return 'en'

def get_match_info(block, offset, length):
    '''
    Extracts match data.
    
    Args:
        offset (int): Number of beginning index of match in the string
        length (int): Length of the match.
        block (logical_block): contains string and metadata of each word
    
    Returns:
        start_page (int): Page number of the beginning of the match
        end_page (int): Page number of the end of the match
        word_index (list): List of word indexes in the match
    '''
    end_offset = offset + length
    word_idxs = []
    start_page = None
    end_page = None

    for word in block.words:
        if word.start_char < end_offset and word.end_char > offset:
            word_idxs.append(word.word_index)
            if start_page is None:
                start_page = word.page_number
            end_page = word.page_number
    if len(word_idxs) >0:
        error_coordinate = (block.words[word_idxs[-1]].bbox[2], block.words[word_idxs[-1]].bbox[3])
    else:
        error_coordinate = (0, 0)
        #print(f"{word.text} {word.page_number} {word.start_char} {end_offset} {word.end_char} {end_offset}")
    return start_page, end_page, word_idxs, error_coordinate

def extract_errors_to_json(matches, name):

    """
    Extracts errors from the list of matches and writes them to a JSON file.
    
    Args:
        matches (list): A list of errors to be extracted.

    Returns:
        None    
    """
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
    """
    Extracts block.content for analysis and its language.
    
    Args:
        block (logical_block): contains string and metadata of each word.

    Returns:
        blocks (list(Block_context)): List contaning Block_context objects.
    """
    blocks_info = []
    for block in blocks.logical_blocks:
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
