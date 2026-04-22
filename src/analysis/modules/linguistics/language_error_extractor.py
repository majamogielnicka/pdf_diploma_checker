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
    polish_messages = {
        'CASING': "Błąd enkapsulacji.",
        'COLLOCATIONS': "Błąd kolokacji.",
        'COMPOUNDING': "Błąd łączenia słów.",
        'GRAMMAR': "Błąd gramatyczny.",
        'MISC': "Różna odmiana.",
        'NONSTANDARD_PHRASES': "Możliwe złe użycie stałego stwierdzenia.",
        'PLAIN_ENGLISH': "Możliwe złe użycie stałego stwierdzenia.",
        'MULTITOKEN_SPELLING': "Błąd pisowni.",
        'TYPOS': "Możliwa literówka.",
        'PROPER_NOUNS': 'Zła pisownia nazwy własnej.',
        'PUNCTUATION': "Błąd interpunkcyjny.",
        'TYPOGRAPHY': "Błąd typograficzny."
    }

    whitespace_counter = 0
    tool_en = language_tool_python.LanguageTool('en-GB')
    tool_en.disabled_categories.add('BRE_STYLE_OXFORD_SPELLING')
    tool_en.disabled_categories.add('MULTITOKEN_SPELLING')
    tool_en.disabled_categories.add('CONFUSED_WORDS')
    tool_en.disabled_rules.add('EN_UNPAIRED_BRACKETS')
    tool_en.disabled_rules.add('COMMA_PERIOD_CONFUSION')
    tool_en.disabled_rules.add('EN_UNPAIRED_QUOTES')
    tool_en.disabled_categories.add('TON_ACADEMIC')
    tool_en.disabled_categories.add('CONFUSED_WORDS')
    tool_en._disabled_categories.add('CREATIVE_WRITING')
    tool_en.disabled_categories.add('REDUNDANCY')
    tool_en.disabled_categories.add('REPETITIONS_STYLE')
    tool_en.disabled_categories.add('SEMATICS')
    tool_en.disabled_categories.add('STYLE')
    tool_pl = language_tool_python.LanguageTool('pl-PL')
    tool_pl.disabled_rules.add('NIETYPOWA_KOMBINACJA_DUZYCH_I_MALYCH_LITER')
    tool_pl.disabled_rules.add('PL_UNPAIRED_BRACKETS')
    tool_pl.disabled_rules.add('SUBST_ADJ_UNIFY')
    tool_pl.disabled_rules.add('ADJ_SUBST_ADJ_UNIFY')
    tool_pl.disabled_rules.add('FORMAT_DZIESIETNY')
    tool_pl.disabled_rules.add('SPACJA_ZA_PRZECINKIEM_DZIESITNYM')

        
    detector = language_detector

    errors = []
    for block in blocks:
        if block.block.type not in {"acronym", "keywords"}:
            contents = block.contents
            text_language = block.language
            matches = tool_pl.check(contents) if text_language == "pl" else tool_en.check(contents)

            new_matches = []
            for match in matches:
                if match.category == 'TYPOGRAPHY' and block.block.type != "paragraph":
                    continue
                if match.category == "TYPOS" and text_language == "pl":
                    word = contents[match.offset:match.offset + match.error_length]
                    if detector.detect_language_of(word) == Language.ENGLISH:
                        en_matches = tool_en.check(word)
                        for en_match in en_matches:
                            en_match.sentence = match.sentence
                            en_match.offset += match.offset
                            en_match.message = polish_messages[en_match.category]
                        new_matches.extend(en_matches)
                        continue
                new_matches.append(match)

        for m in new_matches:
            start_page, end_page, word_idxs, error_coordinate = get_match_info(block.block, m.offset, m.error_length)
            if text_language == 'en':
                message = polish_messages[m.category]
            else:
                message = m.message
                print(match.matched_text)
                print(match.rule_id)
            errors.append(Error_type(
                content=contents[m.offset:m.offset + m.error_length],
                category=m.category,
                message=message,
                offset=m.offset,
                error_length=m.error_length,
                block_id = block.block.block_id,
                page_start = start_page,
                page_end = end_page,
                word_idxs = word_idxs,
                error_coordinate= error_coordinate,
            ))
  
    return errors, whitespace_counter

    




