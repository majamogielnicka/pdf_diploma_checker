from .spacy_helpers import nlp_pl, nlp_en
from spacy.symbols import VERB
from src.analysis.extraction.schema import *
from .exeptions_check import check_quotes
from .helpers import get_match_info, morf, language
from .linguistics_types import Error_type, Analisys_type
from .proper_check import check_if_proper

def sentence_check(blocks):
    '''
    Marks usage of 1st personal form as an error. Creates statistics on passive and active forms of sentences.
    Args:
        blocks (list(Block_context)): List contaning Block_context objects.
    Returns:
        list: A list of matches.
        analisys (Analisys_type): Statistics about sentence structures in the document.
    '''
    sentence_count = 0
    passive_count = 0
    active_count = 0
    verbless_count = 0
    impersonal_count = 0
    checked_matches = []
    for block in blocks:
        if block.language == 'pl':
            nlp = nlp_pl
        else:
            nlp = nlp_en
        text = block.contents
        content = nlp(text)
        for sentence in content.sents:
            passive = False
            is_subject = False
            is_verb = False
            sentence_count += 1
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
                            if not check_quotes(match, text) and not check_if_proper(block.block, match, is_diff = True):
                                checked_matches.append(match)
                if token.dep_ in {'nsubj', 'nsubj:pass'}:
                    is_subject = True
                if token.pos_ in {'VERB', 'AUX'}:
                    is_verb = True    
                #nawet gdy jedna z części zdania jest bierna, całe zdanie złożone uznawane jest za bierne dla przejrzystości wyników.
                if token.dep_ == "aux:pass":
                    passive = True
                    if block.language == 'pl' and not is_subject:
                        #dla zdań biernych, gdy parser nie wykryje podmiotu
                        if any(tok.pos_ in {"NOUN", "PROPN"} and "Case=Nom" in tok.morph for tok in sentence):
                            is_subject = True
                elif token.morph.get("Person") and token.morph.get("Person")[0] == "0":
                    impersonal_count +=1
                #wykrywanie form typu: Mówi się jako bezosobowe
                elif block.language =='pl'and token.text == "się":
                    if token.head.morph.get("Person") and token.head.morph.get("Person")[0] == "3":
                        if not any(child.dep_ == "nsubj" for child in token.head.children):
                            impersonal_count +=1
            match_list = []
            if block.block.type == "paragraph":
                if not is_subject:
                    #zdania z czasownikami niewłaściwymi np. "Na podstawie badań można sformułować wnioski" uznawane są za błąd - nie mają podmiotu domyślnego.
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
                #sprawdzanie czy zdanie jest cytatem, aby nie uwzględniać ich jako błędów.
                if not check_quotes(match, text) and not check_if_proper(block.block, match):
                    checked_matches.append(match)
            if passive:
                passive_count += 1
            elif not is_verb:
                verbless_count += 1
            else: 
                active_count += 1
    if passive_count + active_count > 0:
        passive_ratio = passive_count/(passive_count + active_count)
    else:
        passive_ratio = 0
    analisys = Analisys_type(
        passive_count= passive_count,
        active_count= active_count,
        passive_ratio= f"{round(passive_ratio * 100, 2)}%",
        wrong_person_count= len(checked_matches),
        impersonal_count= impersonal_count,
        sentence_count = sentence_count
    )
    print(f"active:{analisys.active_count} passive:{analisys.passive_count} sum counted:{sentence_count}")
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