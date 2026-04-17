from .linguistics_types import Error_type
from .helpers import add_match

def potential_acronym(text):

    TITLE_PAGE_PHRASES = {
    "PRACA", "MAGISTERSKA", "INŻYNIERSKA", "DYPLOMOWA",
    "STRESZCZENIE", "ABSTRACT", "SŁOWA", "KLUCZOWE",
    "KEYWORDS", "WYKAZ", "SKRÓTÓW", "ABBREVIATIONS",
    "ENGINEERING", "THESIS", "UNIVERSITY", "POLITECHNIKA",
    }

    clean_text = text.strip("():;,.!?[]\n\t ")
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
    if any(char.isupper() for char in clean_text[1:]) and not clean_text[0].isupper():
        return True
    if text.startswith("(") and text.endswith(")"):
        inner = text[1:-1]
        if inner.isupper() and len(inner) >= 2:
            return True
    return False

    return 

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
    category = "ACRONYM_UNDEFINED"
    message = "Skrót nie został zdefiniowany przed jego użyciem."
    matches = []

    proper_names_clean = {p[0].strip("() \n\t.,;:") for p in proper_names} if proper_names else set()
    
    for block in blocks:
        block = block.block
        if block.type in {"acronyms", "heading"}:
            continue
        for word in block.words:
            text = word.text
            clean_text = text.strip("():;,.!?[]\n\t ")
            
            if not potential_acronym(text):
                continue
            if clean_text in proper_names_clean:
                continue

            page = word.page_number
            if clean_text in acronyms_with_definitions:
                acronym = acronyms_with_definitions[clean_text]
                acronym_page, acronym_bbox = acronym[2], acronym[3]

                if (page, word.bbox[1], word.bbox[0]) < (acronym_page, acronym_bbox[1], acronym_bbox[0]):
                    matches.append(add_match(word.text, block.block_id, page, page, word.word_index, word.bbox, category, message))
            else:
                matches.append(add_match(word.text, block.block_id, page, page, word.word_index, word.bbox, category, message))

    return matches