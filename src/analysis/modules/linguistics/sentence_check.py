from .spacy_helpers import nlp_pl, nlp_en
from spacy.symbols import VERB
import spacy
from src.analysis.extraction.schema import *
from .exeptions_check import check_quotes
from .helpers import get_match_info
from .linguistics_types import Error_type, Analisys_type

def sentence_check(blocks, text_language):
    '''
    Marks usage of personal forms of verbs (excluding 3rd) as an error. Creates statistics on passive and active forms of sentences.
    Args:
        text_language (str): The language in which the text is written ("en" for English, "pl" for Polish).
        blocks (FinalDocument): The string of text to be analysed.
    Returns:
        list: A list of matches.
        analisys (Analisys_type): Statistics about sentence structures in the document.
    '''
    passive_count = 0
    active_count = 0
    impersonal_count = 0
    if text_language == 'pl':
        nlp = nlp_pl
    else:
        nlp = nlp_en
    checked_matches = []
    for block in blocks.logical_blocks:
        if isinstance(block, ParagraphBlock):
            text = block.content
        elif isinstance(block, ListBlock):
            text = " ".join(item.text for item in block.items if item.text)
        else:
            continue
        content = nlp(text)
        for idx, sentence in enumerate(content.sents):
            passive = False
            quotes = False
            for token in sentence:
                if token.morph.get("Person") and token.morph.get("Person")[0] not in {'3', '0'}:
                    start_page, end_page, word_idxs = get_match_info(block, token.idx, len(token))
                    match = Error_type(
                    content= token.text,
                    category= "PERSONAL_FORM",
                    message= f"Użycie {token.morph.get("Person")[0]} formy osobowej.",
                    offset= token.idx,
                    error_length= len(token),
                    block_id = block.block_id,
                    page_start = start_page,
                    page_end = end_page,
                    word_idxs = word_idxs,
                )
                    if not check_quotes(match, text):
                        checked_matches.append(match)
                    else:
                        quotes = True

                #for now if even one part of a sentence is passive, whole sentence is marked as passive for clarity of the outcome.
                if token.dep_ == "aux:pass":
                    passive = True
                elif token.morph.get("Person") and token.morph.get("Person")[0] == "0":
                    impersonal_count +=1
                elif text_language =='pl'and token.text == "się":
                    if token.head.morph.get("Person") and token.head.morph.get("Person")[0] == "3":
                        if not any(child.dep_ == "nsubj" for child in token.head.children):
                            impersonal_count +=1
            if passive:
                passive_count += 1
            elif not quotes:
                active_count += 1

    analisys = Analisys_type(
        passive_count= passive_count,
        active_count= active_count,
        passive_ratio= f"{passive_count/(passive_count + active_count)}%",
        wrong_person_count= len(checked_matches),
        impersonal_count= impersonal_count
    )
    return checked_matches, analisys