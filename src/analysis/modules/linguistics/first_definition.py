"""
Moduł odpowiedzialny za ekstrakcję pierwszych definicji skrótów (akronimów) w dokumencie.

"""
import re
import string
from .helpers import language, lemmatization
from .check_acronym import potential_acronym

def initials_match(acronym, definition, proper_names, block = None):

    org_words = [w for w in re.split(r'\s+', definition.strip()) if w]
    def_language = language(definition)
    pl_def = def_language == "pl"

    initials = [w[0] for w in org_words if w and w[0].isupper()]

    if not initials:
        return False

    idx = 0
    matched = True
    for char in acronym:
        if idx < len(initials) and char == initials[idx]:
            idx += 1
        else:
            matched = False
            break

        if idx == len(acronym):
            break

    if matched and idx == len(acronym):
        proper_names.append((acronym, acronym))
        for word_raw in re.split(r'\s+', definition.strip()):
            word_clean = word_raw.strip(string.punctuation + string.whitespace)
            if len(word_clean) >= 2:
                word_lemma, _ = lemmatization(word_clean, def_language)
                proper_names.append((word_clean, word_lemma))
        return True

    if not pl_def and len(org_words) >= len(acronym):
        initials_all = [w[0].upper() for w in org_words if w and w[0].isalpha()]
        if sequence_match(acronym, initials_all):
            proper_names.append((acronym, acronym))
            for word_raw in re.split(r'\s+', definition.strip()):
                word_clean = word_raw.strip(string.punctuation + string.whitespace)
                if len(word_clean) >= 2:
                    word_lemma, _ = lemmatization(word_clean, def_language)
                    proper_names.append((word_clean, word_lemma))
            return True

    if pl_def:
        capitalized_words = [w for w in org_words if w and w[0].isupper() and w[1:].islower() and len(w) > 1]
        if len(capitalized_words) >= max(2, len(acronym)):
            proper_names.append((acronym, acronym))
            for word_raw in re.split(r'\s+', definition.strip()):
                word_clean = word_raw.strip(string.punctuation + string.whitespace)
                if len(word_clean) >= 2:
                    word_lemma, _ = lemmatization(word_clean, def_language)
                    proper_names.append((word_clean, word_lemma))
            return True

    return False

def sequence_match(acronym, initials):
    
    idx = 0
    for letter in initials:
        if idx == len(acronym):
            break
        if letter == acronym[idx]:
            idx += 1
    return idx == len(acronym)


def check_position_if_new(new_acronym, definition, words, block_id, acronyms_with_definitions):

    TITLE_PAGE_PHRASES = {
    "PRACA", "MAGISTERSKA", "INŻYNIERSKA", "DYPLOMOWA",
    "STRESZCZENIE", "ABSTRACT", "SŁOWA", "KLUCZOWE",
    "KEYWORDS", "WYKAZ", "SKRÓTÓW", "ABBREVIATIONS", "OECD"
    "ENGINEERING", "THESIS", "UNIVERSITY", "POLITECHNIKA",
    "WSTĘP", "CEL", "PRACY", "TEORIA", "PRZEGLĄD", "ROZWIĄZAŃ", "OPIS", 
    "WYNIKI", "ZAKOŃCZENIE", "DODATEK", "INSTRUKCJA", "PROGRAMISTY", 
    "DYPLOMU", "UŻYTKOWNIKA", "BIBLIOGRAFIA", "SPIS", "TREŚCI", "RYSUNKÓW", "TABEL"
    }
    new_acronym_clean = new_acronym.strip()
    if new_acronym_clean not in acronyms_with_definitions:
        if new_acronym_clean in TITLE_PAGE_PHRASES:
            return acronyms_with_definitions
            
        words_list = list(words.values()) if isinstance(words, dict) else words
        word_page, word_bbox = None, None
        
        for w in words_list:
            clean_word_text = w.text.strip('.,()[]{}:;"\'')
            if clean_word_text == new_acronym_clean:
                word_page = w.page_number
                word_bbox = w.bbox
                break
                
        if word_page is None:
            for w in words_list:
                clean_word_text = w.text.strip('.,()[]{}:;"\'')
                if clean_word_text.startswith(new_acronym_clean):
                    word_page = w.page_number
                    word_bbox = w.bbox
                    break
        
        if word_page is None and len(words_list) > 0:
            w = words_list[0]
            word_page = w.page_number
            word_bbox = w.bbox
            
        if word_page is not None:
            acronyms_with_definitions[new_acronym_clean] = (definition, block_id, word_page, word_bbox)
            
    return acronyms_with_definitions

def check_first_definition(blocks, proper_names, extracted_acronyms):

    acronyms_with_definitions = {}
    bibliography_re = re.compile(r"^\[\d+\]")
    list_acronyms = re.compile(r'^[A-Z]{2,}\s+[\u2013\u2014\-\u2212:]\s|^((\S+\s){1,4})[\u2013\u2014\-\u2212:]\s')
    paragraph_def_first = re.compile(r'(?<![A-Za-z\u0104\u0106\u0118\u0141\u0143\u00d3\u015a\u0179\u017b\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c])([A-Z\u0104\u0106\u0118\u0141\u0143\u00d3\u015a\u0179\u017b][a-zA-Z\u0104-\u017e\s\-]{2,}?)\s*\(([A-Z]{2,})\)(?=[,\s\.\)\;]|$)',re.UNICODE)
    paragraph_def_first_lower = re.compile(r'(?<![A-Za-z\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c])([a-z\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c][a-zA-Z\u0104-\u017e\s\-]{2,}?)\s*\(([A-Z]{2,})\)(?=[,\s\.\)\;]|$)',re.UNICODE)
    paragraph_def_with_comma = re.compile(r'(?<![A-Za-z\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c])([a-zA-Z\u0104-\u017e][a-zA-Z\u0104-\u017e\s\-]{2,}?)\s*\(([A-Z]{2,})[,\s]',re.UNICODE)
    paragraph_acr_first = re.compile(r'\(([A-Z]{2,})\)\s([A-Z\u00c0-\u017d][a-z\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c\w\s]+)')
    paragraph_ang_pattern = re.compile(r'\b([A-Z]{2,})\s*\((?:ang\.|pol\.|fr\.|niem\.)\s+([^)]{3,}?)\s*\)', re.UNICODE)
    paragraph_ang_pol_pattern = re.compile(r'\b([A-Z]{2,10})\s*\(\s*(?:ang\.|pol\.|niem\.|fr\.|łac\.)?\s*([A-Za-z\u0104-\u017e][A-Za-z\u0104-\u017e\s\-]{3,}?)\s*(?:,|;|\s{2,})', re.UNICODE)
    paragraph_acr_then_expansion = re.compile(r'\b([A-Z]{2,})\s*\(([A-Z][a-zA-ZÀ-Ž][a-zA-ZÀ-Žąćęłńóśźż\s\-]{2,})\)')
    paragraph_acr_quoted = re.compile(r'\b([A-Z]{2,})\s*\(["\u201e\u201c\u00ab\u2018]([A-Za-z][^"\u201d\u00bb\u2019)]{3,}?)["\u201d\u00bb\u2019]\)',re.UNICODE)
    broken_parenthesis_ang = re.compile(r'\b([A-Z]{2,})\s*\(\s*(?:ang\.|pol\.|fr\.|niem\.)\s+([A-Za-z\u0104-\u017e\s\-]{3,}?)\s*(?:\)|,|$)', re.UNICODE)
    broken_parenthesis_acr_dash = re.compile(r'\(\s*([A-Z]{2,})\s*[\-\u2013\u2014:]\s*(?:ang\.|pol\.|fr\.|niem\.)?\s*([A-Za-z\u0104-\u017e\s\-]{3,}?)\s*(?:\)|,|$)', re.UNICODE)
    parenthesis_def_dash_acr = re.compile(r'\(\s*(?:ang\.|pol\.|fr\.|niem\.|łac\.)?\s*([A-Za-z\u0104-\u017e][A-Za-z\u0104-\u017e\s\-]{2,}?)\s*[\-\u2013\u2014]\s*([A-Z]{2,})\s*\)', re.UNICODE)
    broken_no_parenthesis_svm = re.compile(r'\b([A-Z]{2,})\s+([A-Z][a-z]+\s+[A-Z][a-z]+[\w\s\-]*)\s*\)', re.UNICODE)
    paragraph_ang_phrase = re.compile(r'((?:[A-Za-z\u0104-\u017e][A-Za-z\u0104-\u017e\-]*\s+){1,3})\((?:ang\.|pol\.|niem\.|fr\.|\u0142ac\.)\s+([^)]{3,}?)\)', re.UNICODE)
    paragraph_ang_def_acr = re.compile(r'\((?:ang\.|pol\.|niem\.|fr\.)\s+([A-Za-z\u0104-\u017e\s\-,]{3,}?),\s*([A-Z]{2,})\)', re.UNICODE)
    simple_paren_acronym = re.compile(r'([\w][\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s\-]{3,}?)\s\(([A-Z]{2,6})\)',re.UNICODE)
    split = re.compile(r"\s[-\u2013\u2014]\s")

    if extracted_acronyms:
        for item in extracted_acronyms:
            if not item.words:
                item_page = 0
                item_bbox = [0.0, 0.0, 0.0, 0.0]
            else:
                item_page = item.words[0].page_number
                item_bbox = item.words[0].bbox

            initials_match(item.acronym, item.definition, proper_names)
            acronyms_with_definitions[item.acronym] = (item.definition, "official_list", item_page, item_bbox)

    for b in blocks:
        block = b.block
        words = block.words 
        if bibliography_re.search(block.content):
            continue
        if block.type in {"math", "code_snippet", "toc", "tot", "tof"}:
            continue
        if block.type == "list":
            if block.is_bibliography:
                continue
            for item in block.items:
                if list_acronyms.search(item.text):
                    new_acronym = split.split(item.text, 1)
                    new_acronym[0] = new_acronym[0].strip()
                    if len(new_acronym) > 1 and potential_acronym(new_acronym[0]):
                        acronyms_with_definitions = check_position_if_new(new_acronym[0], new_acronym[1].strip(), item.words, block.block_id, acronyms_with_definitions)


        if block.type in ("paragraph", "heading", "list"):
            if block.type == "list" and block.is_bibliography:
                continue
            if '(' in block.content or ')' in block.content:
                text = block.content
                new_acronyms = paragraph_acr_first.findall(text)
                new_acronyms.extend(paragraph_acr_then_expansion.findall(text))
                new_acronyms.extend(paragraph_ang_pattern.findall(text))
                new_acronyms.extend(paragraph_ang_pol_pattern.findall(text))
                new_acronyms.extend(paragraph_acr_quoted.findall(text))
                new_acronyms.extend(broken_parenthesis_ang.findall(text))
                new_acronyms.extend(broken_parenthesis_acr_dash.findall(text))
                new_acronyms.extend(broken_no_parenthesis_svm.findall(text))
                for new_acronym in new_acronyms:
                    for word_raw in re.split(r'\s+', new_acronym[1].strip()):
                        word_clean = word_raw.strip(string.punctuation + string.whitespace)
                        if len(word_clean) >= 2:
                            word_lemma, _ = lemmatization(word_clean, b.language)
                            proper_names.append((word_clean, word_lemma))
                    if initials_match(new_acronym[0], new_acronym[1], proper_names, block):
                        acronyms_with_definitions = check_position_if_new(new_acronym[0], new_acronym[1], words, block.block_id, acronyms_with_definitions)
                for before_phrase, inside_phrase in paragraph_ang_phrase.findall(text):
                    for phrase in (before_phrase, inside_phrase):
                        for word_raw in re.split(r'\s+', phrase.strip()):
                            word_clean = word_raw.strip(string.punctuation + string.whitespace)
                            if len(word_clean) >= 2:
                                word_lemma, _ = lemmatization(word_clean, b.language)
                                proper_names.append((word_clean, word_lemma))
                new_acronyms = paragraph_def_first.findall(text)
                new_acronyms.extend(paragraph_def_with_comma.findall(text))
                new_acronyms.extend(paragraph_def_first_lower.findall(text))
                new_acronyms.extend(parenthesis_def_dash_acr.findall(text))
                for new_acronym in new_acronyms:
                    for word_raw in re.split(r'\s+', new_acronym[0].strip()):
                        word_clean = word_raw.strip(string.punctuation + string.whitespace)
                        if len(word_clean) >= 2:
                            word_lemma, _ = lemmatization(word_clean, b.language)
                            proper_names.append((word_clean, word_lemma))
                    if initials_match(new_acronym[1], new_acronym[0], proper_names, block):
                        acronyms_with_definitions = check_position_if_new(new_acronym[1], new_acronym[0], words, block.block_id, acronyms_with_definitions)

                for definition, acronym in paragraph_ang_def_acr.findall(text):
                    if potential_acronym(acronym):
                        for word_raw in re.split(r'\s+', definition.strip()):
                            word_clean = word_raw.strip(string.punctuation)
                            if len(word_clean) >= 2:
                                word_lemma, _ = lemmatization(word_clean, b.language)
                                proper_names.append((word_clean, word_lemma))
                        proper_names.append((acronym, acronym))
                        acronyms_with_definitions = check_position_if_new(acronym, definition, words, block.block_id, acronyms_with_definitions)

                for definition, acronym in simple_paren_acronym.findall(text):
                    def_words = definition.strip().split()
                    if potential_acronym(acronym) and len(def_words) >= 2:
                        for word_raw in def_words:
                            word_clean = word_raw.strip(string.punctuation)
                            if len(word_clean) >= 2:
                                word_lemma, _ = lemmatization(word_clean, b.language)
                                proper_names.append((word_clean, word_lemma))
                        proper_names.append((acronym, acronym))
                        acronyms_with_definitions = check_position_if_new(acronym, definition, words, block.block_id, acronyms_with_definitions)
                
                for acronym, definition in paragraph_ang_pattern.findall(text):
                    if potential_acronym(acronym):
                        proper_names.append((acronym, acronym))
                        acronyms_with_definitions = check_position_if_new(acronym, definition, words, block.block_id, acronyms_with_definitions)
    
    return acronyms_with_definitions, proper_names