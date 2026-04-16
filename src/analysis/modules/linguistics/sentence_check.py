from .spacy_helpers import nlp_pl, nlp_en
from spacy.symbols import VERB
from src.analysis.extraction.schema import *
from .exeptions_check import check_quotes
from .helpers import get_match_info, morf, language
from .linguistics_types import Error_type, Analisys_type
from .proper_check import check_if_proper
def sentence_check(blocks):
    '''
    Marks usage of personal forms of verbs (excluding 3rd) as an error. Creates statistics on passive and active forms of sentences.
    Args:
        blocks (list(Block_context)): List contaning Block_context objects.
    Returns:
        list: A list of matches.
        analisys (Analisys_type): Statistics about sentence structures in the document.
    '''
    sentence_count = 0
    passive_count = 0
    active_count = 0
    skipped = 0
    impersonal_count = 0
    checked_matches = []
    for block in blocks:
        if block.language == 'pl':
            nlp = nlp_pl
        else:
            nlp = nlp_en
        text = block.contents
        content = nlp(text)
        skip = False
        sentence_count = len(list(content.sents))
        if sentence_count < 3:
            skip = True
        for sentence in content.sents:
            passive = False
            quotes = False
            is_subject = False
            is_verb = False
            for token in sentence:
                if token.morph.get("Person"):
                    is_subject = True
                    if token.morph.get("Person")[0] == '1':
                        to_add = True
                        if block.language == 'pl':
                            to_add = morfeusz_check(token.text)
                        if to_add:
                            start_page, end_page, word_idxs, error_coordinate = get_match_info(block.block, token.idx, len(token))
                            match = Error_type(
                            content= token.text,
                            category= "PERSONAL_FORM",
                            message= f"Użycie {token.morph.get("Person")[0]} formy osobowej.",
                            offset= token.idx,
                            error_length= len(token),
                            block_id = block.block.block_id,
                            page_start = start_page,
                            page_end = end_page,
                            word_idxs = word_idxs,
                            error_coordinate= error_coordinate
                            )   
                            if not check_quotes(match, text):
                                checked_matches.append(match)
                            else:
                                quotes = True
                if token.pos_ in {'VERB', 'AUX'}:
                    is_verb = True    
                #for now if even one part of a sentence is passive, whole sentence is marked as passive for clarity of the outcome.
                if token.dep_ == "aux:pass":
                    passive = True
                elif token.morph.get("Person") and token.morph.get("Person")[0] == "0":
                    impersonal_count +=1
                elif block.language =='pl'and token.text == "się":
                    if token.head.morph.get("Person") and token.head.morph.get("Person")[0] == "3":
                        if not any(child.dep_ == "nsubj" for child in token.head.children):
                            impersonal_count +=1
            match_list = []
            if not skip:
                if not is_subject:
                    match_list.append(("NO_SUBJECT", "Brak podmiotu w zdaniu."))
                if not is_verb:
                    match_list.append(("NO_VERB", "Brak orzeczenia w zdaniu."))
            for category, message in match_list:
                start_page, end_page, word_idxs, error_coordinate = get_match_info(block.block, sentence[0].idx, len(sentence))
                match = Error_type(
                content= text[sentence[0].idx:(sentence[0].idx+len(sentence.text))],
                category=  category,
                message= message,
                offset= sentence[0].idx,
                error_length= len(sentence.text),
                block_id = block.block.block_id,
                page_start = start_page,
                page_end = end_page,
                word_idxs = word_idxs,
                error_coordinate= error_coordinate
                )
                if check_quotes(match, text):
                    quotes = True
                elif check_if_proper(block.block, match):
                    quotes = True
                    #print(match.content)
                elif block.block.type != "paragraph":
                    pass
                else:
                    checked_matches.append(match)
            if passive:
                passive_count += 1
            elif not quotes:
                active_count += 1
            else: 
                #print(sentence.text)
                skipped += 1
    if passive_count + active_count > 0:
        passive_ratio = passive_count/(passive_count + active_count)
    else:
        passive_ratio = 0
    analisys = Analisys_type(
        passive_count= passive_count,
        active_count= active_count,
        passive_ratio= f"{passive_ratio}%",
        wrong_person_count= len(checked_matches),
        impersonal_count= impersonal_count
    )
    #print(f"active:{analisys.active_count} passive:{analisys.passive_count} skipped:{skipped} sum sents:{sentence_count} sum counted:{analisys.active_count + analisys.passive_count + skipped}")
    return checked_matches, analisys

def morfeusz_check(text):
    '''
    Additionally checks matches found by initial personal form check.
    Args:
        text (str): Text content of found match.
    Returns:
        bool: True if personal form has been legitimatized.
    '''
    personal_tags = {"pri", "sec", "ppron12"}
    analysis = morf.analyse(text)
    for interpretation in analysis:
        tags = set(interpretation[2][2].split(":"))
        if len(set(personal_tags).intersection(tags)) > 0:
            return True
    return False