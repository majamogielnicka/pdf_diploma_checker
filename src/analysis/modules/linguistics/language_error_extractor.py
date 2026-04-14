import language_tool_python
from lingua import Language, LanguageDetectorBuilder
from .linguistics_types import Error_type
from src.analysis.extraction.schema import *
from .helpers import get_match_info, language_detector

def language_tool_analisys(blocks):
    """
    Performs an initial grammar and spelling check in the specified language. Detects double spaces and interpunction errors.
    
    Args:
        blocks (list(Block_context)): List contaning Block_context objects.
    
    Returns:
        list: A list of matches.
    """
    whitespace_counter = 0
    tool_en = language_tool_python.LanguageTool('en-GB')
    tool_pl = language_tool_python.LanguageTool('pl-PL')
    tool_pl.disabled_rules.add('NIETYPOWA_KOMBINACJA_DUZYCH_I_MALYCH_LITER')
        
    detector = language_detector

    errors = []
    for block in blocks:
        contents = block.contents
        text_language = block.language
        matches = tool_pl.check(contents) if text_language == "pl" else tool_en.check(contents)

        new_matches = []
        for match in matches:
            if match.rule_id == 'WHITESPACE_RULE':
                whitespace_counter = whitespace_counter + 1
                print(match)
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
            start_page, end_page, word_idxs = get_match_info(block.block, m.offset, m.error_length)
            errors.append(Error_type(
                content=contents[m.offset:m.offset + m.error_length],
                category=m.category,
                message=m.message,
                offset=m.offset,
                error_length=m.error_length,
                block_id = block.block.block_id,
                page_start = start_page,
                page_end = end_page,
                word_idxs = word_idxs,
            ))
    print(whitespace_counter)    
    return errors, whitespace_counter

    




