import language_tool_python
from lingua import Language, LanguageDetectorBuilder
import os
import json
from src.linguistics.linguistics_types import Error_type
import dataclasses
from src.redaction.schema import *
from src.linguistics.helpers import get_match_info

def language_tool_analisys(text_language, blocks):
    
    """
    Performs an initial grammar and spelling check in the specified language. Detects double spaces and interpunction errors.
    
    Args:
        text_language (str): The language in which the text is written ("en" for English, "pl" for Polish).
        blocks (FinalDocument): The string of text to be analysed.
    
    Returns:
        list: A list of matches.
    """
    whitespace_counter = 0
    tool_en = language_tool_python.LanguageTool('en-GB')
    tool_pl = language_tool_python.LanguageTool('pl-PL') if text_language == "pl" else None
    if text_language == "pl":
        tool_pl.disabled_rules.add('NIETYPOWA_KOMBINACJA_DUZYCH_I_MALYCH_LITER')

    languages = [Language.ENGLISH, Language.POLISH]
    detector = LanguageDetectorBuilder.from_languages(*languages).build()

    errors = []
    for block in blocks.logical_blocks:
        if isinstance(block, ParagraphBlock):
            contents = block.content
        # elif isinstance(block, ListItem):
        #     contents = block.text
        else:
            continue

        matches = tool_pl.check(contents) if text_language == "pl" else tool_en.check(contents)

        new_matches = []
        for match in matches:
            if match.rule_id == 'WHITESPACE_RULE':
                whitespace_counter = whitespace_counter + 1
            if match.category == "TYPOS" and text_language == "pl":
                word = contents[match.offset:match.offset + match.error_length]
                if detector.detect_language_of(word) == Language.ENGLISH:
                    en_matches = tool_en.check(word)
                    for en_match in en_matches:
                        en_match.sentence = match.sentence
                        en_match.offset += match.offset
                    new_matches.extend(en_matches)
                    continue
            new_matches.append(match)

        for m in new_matches:
            start_page, end_page, word_idxs = get_match_info(block, m.offset, m.error_length)
            errors.append(Error_type(
                content=contents[m.offset:m.offset + m.error_length],
                category=m.category,
                message=m.message,
                offset=m.offset,
                error_length=m.error_length,
                block_id = block.block_id,
                page_start = start_page,
                page_end = end_page,
                word_idxs = word_idxs,
            ))
    return errors, whitespace_counter

    
def extract_errors_to_json(matches):

    """
    Extracts errors from the list of matches and writes them to a JSON file.
    
    Args:
        matches (list): A list of errors to be extracted.

    Returns:
        None    
    """
    #check only milestone 1 categories
    #checked_categories = {'PUNCTUATION', 'LIST_COHERENCE', 'DECIMAL', 'TYPOGRAPHY'}
    num = 0
    for match in matches:
        #if match.category in checked_categories:
            num += 1  
            match_serialized = dataclasses.asdict(match)
            f = open(os.path.join(os.path.dirname(__file__), "json",f"error_file_{num}.json"), "w", encoding="utf-8")
            json.dump(match_serialized, f, ensure_ascii=False, indent=4)





