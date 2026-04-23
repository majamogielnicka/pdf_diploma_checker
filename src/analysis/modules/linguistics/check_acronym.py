from .helpers import add_match
import re

def potential_acronym(text):

    TITLE_PAGE_PHRASES = {
    "PRACA", "MAGISTERSKA", "INŻYNIERSKA", "DYPLOMOWA",
    "STRESZCZENIE", "ABSTRACT", "SŁOWA", "KLUCZOWE",
    "KEYWORDS", "WYKAZ", "SKRÓTÓW", "ABBREVIATIONS",
    "ENGINEERING", "THESIS", "UNIVERSITY", "POLITECHNIKA",
    "WSTĘP", "CEL", "PRACY", "TEORIA", "PRZEGLĄD", "ROZWIĄZAŃ", "OPIS", 
    "WYNIKI", "ZAKOŃCZENIE", "DODATEK", "INSTRUKCJA", "PROGRAMISTY", 
    "DYPLOMU", "UŻYTKOWNIKA", "BIBLIOGRAFIA", "SPIS", "TREŚCI", "RYSUNKÓW", "TABEL"
    }
    clean_text = text.strip("():;,.!?[]\n\t \"„”«»“‟‘’")
    if re.match(r'^([A-Z]\.){1,}[A-Z]?$', clean_text):
        return False
    if len(clean_text) < 2 or len(clean_text) > 10:
        return False
    if clean_text.islower():
        return False
    if clean_text.isdigit():
        return False
    if clean_text in TITLE_PAGE_PHRASES:
        return False
    if clean_text.isupper() and any(char.isalpha() for char in clean_text):
        return True
    # if any(char.isupper() for char in clean_text[1:]) and not clean_text[0].isupper():
    #     return True
    if text.startswith("(") and text.endswith(")"):
        inner = text[1:-1]
        if inner.isupper() and len(inner) >= 2:
            return True
    return False

def check_if_was_defined(blocks, acronyms_with_definitions, proper_names):

    """ 
    Checks if the acronym was defined before the current block.
    
    Args:
        blocks (list): List of blocks.
        acronyms_with_definitions (dict): Dictionary of acronyms and their definitions.
        proper_names (set): Set of valid proper names.
    
    Returns:
        list: List of error objects.
    """
    
    GLOBAL_ACRONYMS = {
        "USA", "EU", "UN", "NATO", "WHO", "UNESCO", "ONZ", "UE", "PL", "EN", 
        "IT", "PC", "USB", "GPS", "WiFi", "PDF", "PhD", "MSc", "BSc", "SI", "CEO"
    }
    QUOTE_MARKS = {'"', '„', '”', '«', '»', '“', '‟', '‘', '’'}
    category = "ACRONYM_UNDEFINED"
    message = "Skrót nie został zdefiniowany przed jego użyciem."
    matches = []
    reported_acronyms = set()
    no_parenthesis = re.compile(r'\b([A-Z]{2,})\s*\((?:ang\.|pol\.|fr\.)\s+([^)]{3,}?)(?=[,;]|\s{2,}[A-Z]{2})', re.UNICODE)
    roman_numeral = re.compile(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$')
    #proper_names_clean = {p[0].strip("() \n\t.,;:") for p in proper_names if not p[0].strip("() \n\t.,;:").isupper()} if proper_names else set()
    
    for block in blocks:
        block = block.block
        if block.type in {"paragraph", "list"}:
            for word in block.words:
                text = word.text
                clean_text = text.strip("|():;,.!?[]\n\t \"„”«»“‟‘’")
                if any(c in QUOTE_MARKS for c in text):
                    continue
                if not potential_acronym(text):
                    continue
                if clean_text[0].isdigit():
                    continue
                if roman_numeral.match(clean_text):
                    continue
                # if clean_text in proper_names_clean:
                #     continue
                if clean_text in GLOBAL_ACRONYMS:
                    continue
                page = word.page_number
                if no_parenthesis.search(block.content[word.start_char:word.start_char:]):
                    continue   
                if clean_text in acronyms_with_definitions:
                    acronym = acronyms_with_definitions[clean_text]
                    acronym_page, acronym_bbox = acronym[2], acronym[3]

                    if (page, word.bbox[1], word.bbox[0]) < (acronym_page, acronym_bbox[1], acronym_bbox[0]):
                        if clean_text not in reported_acronyms:
                            reported_acronyms.add(clean_text)
                            matches.append(add_match(word.text, block.block_id, page, page, [word.word_index], [{"page": page, "coordinates": list(word.bbox)}], category, message))
                else:
                    if clean_text not in reported_acronyms:
                        reported_acronyms.add(clean_text)
                        matches.append(add_match(word.text, block.block_id, page, page, [word.word_index], [{"page": page, "coordinates": list(word.bbox)}], category, message))
    return matches