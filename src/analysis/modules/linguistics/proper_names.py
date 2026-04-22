from .spacy_helpers import nlp_pl, nlp_en, lemmatization
import re


def get_proper_names(blocks):
    """
    Extracts proper names and recognized entities from the document using spaCy.
    
    Args:
        document (FinalDocument): The document structure.
        text_language (str): The language code of the text.
        
    Returns:
        set: A set containing unique valid proper names extracted from the text.
    """


    TITLE_PAGE_PHRASES = {
    "PRACA", "MAGISTERSKA", "INŻYNIERSKA", "DYPLOMOWA",
    "STRESZCZENIE", "ABSTRACT", "SŁOWA", "KLUCZOWE",
    "KEYWORDS", "WYKAZ", "SKRÓTÓW", "ABBREVIATIONS",
    "ENGINEERING", "THESIS",
    }
    SKIP_LABELS_EN = {"TIME", "DATE", "CARDINAL", "MONEY", "PERCENT", "QUANTITY", "ORDINAL"}
    SKIP_LABEL_PL = {"date", "time"}
    proper_names = []

    previous_check = re.compile(r"^[A-Z].$")
    split_key = re.compile(":")
    split = re.compile(",|;")
    search_keywords = re.compile(r'(?i)(?:keywords|słowa kluczowe)\s*:\s*(.*)')
    search_space = re.compile(r"\s")
    bibliography = re.compile(r"^\[\d+\]")

    for block in blocks:
        previous = None

        if bibliography.findall(block.contents):
            continue
        if any(phrase in block.contents for phrase in TITLE_PAGE_PHRASES):
            continue
        if block.block.type in ("paragraph", "heading", "list", "acronyms"):

            if block.language == "pl":
                nlp = nlp_pl
                text = nlp(block.contents)
                for ent in text.ents:
                    ent_text = ent.text.strip("(),.:;[]\n\t ")
                    if not ent.label_ or ent.label_ in SKIP_LABEL_PL or len(ent_text) < 2:
                        continue
                    if previous is not None and (previous_check.findall(previous.text) or previous.label_ == "PERSON") and ent.label_ == "PERSON":
                        previous = ent
                        ent_text = previous.text + " " + ent_text
                        if proper_names:
                            proper_names.pop(-1)
                    ent_lemma, is_found = lemmatization(ent_text, block.language)
                    proper_names.append((ent_text, ent_lemma))  

            elif block.language == "en":
                nlp = nlp_en
                text = nlp(block.contents)
                for ent in text.ents:
                    ent_text = ent.text.strip("(),.:;[]\n\t ")   
                    if not ent.label_ or ent.label_ in SKIP_LABELS_EN or len(ent_text) < 2:
                        continue
                    if previous is not None and (previous_check.findall(previous.text) or previous.label_ == "PERSON") and ent.label_ == "PERSON":
                        previous = ent
                        ent_text = previous.text + " " + ent_text
                        if proper_names:
                            proper_names.pop(-1)
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
    proper_names = set(proper_names)
    return proper_names