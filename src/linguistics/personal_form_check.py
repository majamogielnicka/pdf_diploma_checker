from src.linguistics.spacy_helpers import nlp_pl, nlp_en
from spacy.symbols import VERB
import spacy
from src.redaction.schema import *
from src.linguistics.exeptions_check import check_quotes
from src.linguistics.helpers import get_match_info
from src.linguistics.linguistics_types import Error_type

def personal_form_check(blocks, text_language):
    '''
    Checks person of each verb in text, adds an error if person is not zero (impersonal) or third.
    Args:
        text_language (str): The language in which the text is written ("en" for English, "pl" for Polish).
        blocks (FinalDocument): The string of text to be analysed.
    Returns:
        list: A list of matches.
    '''
    if text_language == 'pl':
        nlp = nlp_pl
    else:
        nlp = nlp_en
    checked_matches = []
    for block in blocks.logical_blocks:
        potential_matches = []
        if isinstance(block, ParagraphBlock):
            text = block.content
        elif isinstance(block, ListBlock):
            text = " ".join(item.text for item in block.items if item.text)
        else:
            continue
        content = nlp(text)
        for token in content:
            if token.pos == VERB:
                start_page, end_page, word_idxs = get_match_info(block, token.idx, len(token))
                if token.morph.get("Person") and token.morph.get("Person")[0] not in {'3', '0'}:
                    match = (Error_type(
                    content= token.text,
                    category= "PERSONAL_FORM",
                    message= f"Użycie czasownika w {token.morph.get("Person")[0]} formie osobowej.",
                    offset= token.idx,
                    error_length= len(token),
                    block_id = block.block_id,
                    page_start = start_page,
                    page_end = end_page,
                    word_idxs = word_idxs,
                ))
                    if not check_quotes(match, text):
                        checked_matches.append(match)
                
    return checked_matches
