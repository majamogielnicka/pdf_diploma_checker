'''
Analiza składni zdań, wydobywanie pierwszej formy osobowej z tekstu i oznaczanie jako błąd
jeśli w pliku json nie jest wskazane inaczej oraz wydobywanie i 
oznaczanie jako błąd zdań w praragrafach niezawierających podmiotu lub orzeczenia.
'''
from analysis.extraction.schema import *
from .exeptions_check import check_quotes
from .helpers import get_match_info, morf, language, nlp_pl, nlp_en
from .linguistics_types import Error_type, Analisys_type
from .proper_check import check_if_proper
import re

#ostateczny fallback przy edge case złego wykrycia podpisów, aby nie tworzyć FP z NO_VERB, NO_SUBJECT.
DESCRIPTION_WHITELIST= {"wersja", "wersji", "wersjom", "wersjach", "wersję", "wer","wersją", "wersje", "wersjami", "rys", "rysunek", "rysunkom", "rysunkach", "rysunku", "tabela", "tabeli", "tabelom", "tabelach", "tab",
                     "wykres", "wykresu", "wykresom", "wykresowi", "wykresem", "wykresie", "wykresach", "wyk", "rozdziale", "rozdział", "rozdziały", "rozdziału", "rozdziałem", "rozdziałach", "roz", "rozdz", "rozdziałów", 
                     "obraz", "obr", "obrazie", "obrazu", "obrazowi", "obrazach", "obrazem","obrazom", 
                     "wzór", "wzoru", "wzorowi", "wzory", "wzorom", "wzorach", "wzorami", "wzorem", "wzorze",
                     "równanie", "równaniu", "równaniach", "równaniami", "równaniom", "równania", "równaniem", "rów", "listing"}

def sentence_check(blocks, check_first_person=True):
    sentence_count = 0
    passive_count = 0
    active_count = 0
    verbless_count = 0
    impersonal_count = 0
    checked_matches = []
    for block in blocks:
        if block.block.type == "paragraph":
            if block.language == 'pl':
                nlp = nlp_pl
            else:
                nlp = nlp_en
            text = block.contents
            content = nlp(text)
            for sentence in content.sents:
                first_upper = None
                if sum(1 for letter in sentence.text if letter.isalpha()) < 15:
                    continue
                for letter in sentence.text:
                    if letter.isalpha():
                        first_upper = letter
                        break
                if first_upper is None or not first_upper.isupper():
                    continue
                if re.search(r'\.[ .]{4,}', block.contents):
                    continue
                passive = False
                is_subject = False
                is_verb = False
                is_impersonal = False
                sentence_count += 1
                for token in sentence:
                    if token.morph.get("Person"):
                        is_subject = True
                        if check_first_person and token.morph.get("Person")[0] == '1':
                            to_add = True
                            if block.language == 'pl':
                                to_add = morfeusz_check(token.text)
                            if token.idx > 0 and (text[token.idx - 1] == '-'):
                                to_add = False
                            elif (token.idx + len(token) + 1) < len(text) and (text[token.idx + len(token)] == '-'):
                                to_add = False
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
                                if not check_quotes(match.offset, match.offset + match.error_length, text) and not check_if_proper(block.block, match, is_diff = True):
                                    checked_matches.append(match)
                    if token.dep_ in {'nsubj', 'nsubj:pass', 'nsubjpass', 'attr'}:
                        is_subject = True
                    if token.pos_ in {'VERB', 'AUX'}:
                        is_verb = True    
                    #nawet gdy jedna z części zdania jest bierna, całe zdanie złożone uznawane jest za bierne dla przejrzystości wyników.
                    if token.dep_ == "aux:pass":
                        passive = True
                    #wykrywanie form typu: Mówi się jako bezosobowe
                    if token.morph.get("Person") and token.morph.get("Person")[0] == "0":
                        is_impersonal = True
                    elif block.language =='pl'and token.text == "się":
                        if token.head.morph.get("Person") and token.head.morph.get("Person")[0] == "3":
                            if not any(child.dep_ == "nsubj" for child in token.head.children):
                                is_impersonal = True
                if block.language == 'pl' and not is_subject and passive:
                    #dla zdań biernych, gdy parser nie wykryje podmiotu
                    if any(tok.pos_ in {"NOUN", "PROPN"} and "Case=Nom" in tok.morph for tok in sentence):
                        is_subject = True
                match_list = []
                if description_exclude_backup(sentence.text):
                    continue
                if not is_subject:
                    #zdania z czasownikami niewłaściwymi np. "Na podstawie badań można sformułować wnioski" uznawane są za błąd - nie mają podmiotu domyślnego.
                    match_list.append(("NO_SUBJECT", "Brak podmiotu w zdaniu."))
                if not is_verb:
                    match_list.append(("NO_VERB", "Brak orzeczenia w zdaniu."))
                for category, message in match_list:
                    start_page, end_page, word_idxs, error_coordinate = get_match_info(block.block, sentence[0].idx, len(sentence.text))
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
                    if not check_quotes(match.offset, match.offset + match.error_length, text) and not check_if_proper(block.block, match, is_diff=True) and not definicion(block.block, word_idxs, sentence.text):
                        checked_matches.append(match)
                if passive:
                    passive_count += 1
                elif not is_verb:
                    verbless_count += 1
                else: 
                    active_count += 1
                if is_impersonal:
                    impersonal_count +=1
    if passive_count + active_count + verbless_count > 0:
        passive_ratio = round(passive_count/(passive_count + active_count + verbless_count) * 100)
        verbless_ratio = round(verbless_count/(passive_count + active_count + verbless_count) * 100)
    else:
        passive_ratio = 0
        verbless_ratio = 0

    active_ratio = 100 - passive_ratio - verbless_ratio
    analisys = Analisys_type(
        active_ratio = f"{active_ratio}%",
        passive_ratio= f"{passive_ratio}%",
        verbless_ratio= f"{verbless_ratio}%"
    )
    # print(f'active: {analisys.active_ratio}, {active_count} passive: {analisys.passive_ratio}, {passive_count} verbless: {analisys.verbless_ratio}, {verbless_count} count: {sentence_count}')
    return checked_matches, analisys

def morfeusz_check(text):
    personal_tags = {"pri", "sec", "ppron12"}
    analysis = morf.analyse(text)
    for interpretation in analysis:
        tags = set(interpretation[2][2].split(":"))
        if len(set(personal_tags).intersection(tags)) > 0:
            return True
    return False

def definicion(block, word_idxs, sentence_text):
    if not word_idxs:
        return False
    pattern = r'^\s*\w[\w\s]*[:-–]'
    if block.words[word_idxs[0]].bold and re.match(pattern, sentence_text):
        return True
    return False

def description_exclude_backup(sentence_text):
    words = sentence_text.split()
    if len(words) < 3:
        return True
    if words[0].lower() in DESCRIPTION_WHITELIST and not words[1].isalpha():
        # print(f'{sentence_text} excluded')
        return True
    elif not words[0].isalpha() and words[1][0].isupper():
        # print(f'{sentence_text} excluded')
        return True
    return False