"""
Moduł ekstrakcji nazw własnych i słów kluczowych z dokumentu.

"""
from .helpers import nlp_pl, nlp_en, lemmatization
import re


def get_proper_names(blocks):

    TITLE_PAGE_PHRASES = {
    "PRACA", "MAGISTERSKA", "INŻYNIERSKA", "DYPLOMOWA",
    "STRESZCZENIE", "ABSTRACT", "SŁOWA", "KLUCZOWE",
    "KEYWORDS", "WYKAZ", "SKRÓTÓW", "ABBREVIATIONS",
    "ENGINEERING", "THESIS", "UNIVERSITY", "POLITECHNIKA",
    "WSTĘP", "CEL", "PRACY", "TEORIA", "PRZEGLĄD", "ROZWIĄZAŃ", "OPIS", 
    "WYNIKI", "ZAKOŃCZENIE", "DODATEK", "INSTRUKCJA", "PROGRAMISTY", 
    "DYPLOMU", "UŻYTKOWNIKA", "BIBLIOGRAFIA", "SPIS", "TREŚCI", "RYSUNKÓW", 
    "TABEL", "LISTA", "SYMBOLI"
    }
    SKIP_LABELS_EN = {"TIME", "DATE", "CARDINAL", "MONEY", "PERCENT", "QUANTITY", "ORDINAL"}
    SKIP_LABEL_PL = {"date", "time"}
    BIB_LABELS_EN = {"PERSON", "WORK_OF_ART", "GPE", "ORG" }
    BIB_LABELS_PL = {"persName", "placeName", "orgName"}
    proper_names = []

    # previous_check = re.compile(r"^[A-Z].$")
    # split_key = re.compile(":")
    split = re.compile(",|;")
    search_keywords = re.compile(r'(?i)(?:keywords|słowa kluczowe)\s*:\s*(.*)')
    search_space = re.compile(r"\s")
    bibliography = {
        "people": [],
        "organizations": [],
        "places": [],
        "work": [],
    }

    for block in blocks:
        block_type = block.block.type
        is_bib = block.block.is_bibliography if block_type == "list" else False
        if any(phrase in block.contents for phrase in TITLE_PAGE_PHRASES):
            continue
        if block_type in ("paragraph", "heading", "list", "acronyms"): 
            if block.language == "pl":
                nlp = nlp_pl
                text = nlp(block.contents)
                for ent in text.ents:
                    ent_text = ent.text.strip("(),.:;[]\n\t ")
                    if block_type == "list" and is_bib:
                        if not ent.label_ or not ent.label_ in BIB_LABELS_PL:
                            continue
                        if ent.label_ == "persName":
                            bibliography["people"].append(ent_text)
                        elif ent.label_ == "placeName":
                            bibliography["places"].append(ent_text)
                        elif ent.label_ == "orgName":
                            bibliography["organizations"].append(ent_text)
                    if not ent.label_ or ent.label_ in SKIP_LABEL_PL or len(ent_text) < 2:
                        continue
                    ent_lemma, is_found = lemmatization(ent_text, block.language)
                    proper_names.append((ent_text, ent_lemma))

            if block.language == "en":
                nlp = nlp_en
                text = nlp(block.contents)
                for ent in text.ents:
                    ent_text = ent.text.strip("(),.:;[]\n\t ")
                    if block_type == "list" and is_bib:  
                        if not ent.label_ or not ent.label_ in BIB_LABELS_EN:
                            continue 
                        if ent.label_ == "PERSON":
                            bibliography["people"].append(ent_text)
                        elif ent.label_ == "GPE":
                            bibliography["places"].append(ent_text)
                        elif ent.label_ == "ORG":
                            bibliography["organizations"].append(ent_text)
                        elif ent.label_ == "WORK_OF_ART":
                            bibliography["work"].append(ent_text)
                    if not ent.label_ or ent.label_ in SKIP_LABELS_EN or len(ent_text) < 2:
                        continue
                    ent_lemma, is_found = lemmatization(ent_text, block.language)
                    proper_names.append((ent_text, ent_lemma))

        if block.block.type in ("keywords", "paragraph"):
            keyword_match = search_keywords.search(block.contents)
            if keyword_match:
                keywords_text = keyword_match.group(1)
                keywords = split.split(keywords_text)
                keywords_lemma = []
                for keyword in keywords:
                    keyword = keyword.strip(" \n\t.,;:")
                    if len(keyword) < 2:
                        continue
                    if search_space.search(keyword):
                        keyword_lemma = keyword
                    else:
                        keyword_lemma, is_found = lemmatization(keyword, block.language)
                    keywords_lemma.append((keyword, keyword_lemma))
                proper_names.extend(keywords_lemma)
    return proper_names, bibliography