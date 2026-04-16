from .spacy_helpers import nlp_pl, nlp_en, lemmatization
import re


def get_proper_names(document, text_language):
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

    if text_language == "pl":
        nlp = nlp_pl
    else:
        nlp = nlp_en

    for block in document.logical_blocks:
        previous = None

        if bibliography.findall(block.content):
            continue
        if any(phrase in block.content for phrase in TITLE_PAGE_PHRASES):
            continue
        if block.type in ("paragraph", "heading", "list", "acronyms"):

            if text_language == "pl":
                text = nlp(block.content)
                for ent in text.ents:
                    ent_text = ent.text.strip("(),.:;[]\n\t ")
                    if not ent.label_ or ent.label_ in SKIP_LABEL_PL or len(ent_text) < 2:
                        continue
                    if previous is not None and (previous_check.findall(previous.text) or previous.label == "PERSON") and ent.label_ == "PERSON":
                        previous = ent
                        ent_text = previous.text + " " + ent_text
                        proper_names.pop(-1)
                    ent_lemma, is_found = lemmatization(ent_text, text_language)
                    proper_names.append((ent_text, ent_lemma))  

            elif text_language == "en":
                text = nlp(block.content)
                for ent in text.ents:
                    ent_text = ent.text.strip("(),.:;[]\n\t ")   
                    if not ent.label_ or ent.label_ in SKIP_LABELS_EN or len(ent_text) < 2:
                        continue
                    if previous is not None and (previous_check.findall( previous.text) or previous.label == "PERSON") and ent.label_ == "PERSON":
                        previous = ent
                        ent_text = previous.text + " " + ent_text
                        proper_names.pop(-1)
                    ent_lemma, is_found = lemmatization(ent_text, text_language)
                    proper_names.append((ent_text, ent_lemma))    

        if block.type in ("keywords", "paragraph"):
            keyword_match = search_keywords.search(block.content)
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
                        keyword_lemma, is_found = lemmatization(keyword, text_language)
                    #print("Keyword: ", keyword, "Lemma: ", keyword_lemma, "\n")
                    keywords_lemma.append((keyword, keyword_lemma))
                proper_names.extend(keywords_lemma)
                #print("keywords_lemma: ", keywords_lemma)
    proper_names = set(proper_names)
    #print("Proper names: ", {proper[0] for proper in proper_names})
    return proper_names