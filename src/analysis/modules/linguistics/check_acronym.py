from .linguistics_types import Error_type

def add_match(word, block_id):

    """
    Creates an error object for a specific list item.
    
    Args:
        items_by_id (dict): Dictionary of items by ID.
        num (int): Item ID.
    
    Returns:
        Error_type: Error type object.
    """
    return Error_type(
                content = word.text,
                category = "ACRONYM_UNDEFINED",
                message = "The acronym does not have any definition before",
                offset = 0,
                error_length = len(word.text),
                block_id = block_id,
                page_start = word.page_number ,
                page_end = word.page_number,
                word_idxs = word.word_index
            )

def potential_acronym(text):

    TITLE_PAGE_PHRASES = {
    "PRACA", "MAGISTERSKA", "INŻYNIERSKA", "DYPLOMOWA",
    "STRESZCZENIE", "ABSTRACT", "SŁOWA", "KLUCZOWE",
    "KEYWORDS", "WYKAZ", "SKRÓTÓW", "ABBREVIATIONS",
    "ENGINEERING", "THESIS", "UNIVERSITY", "POLITECHNIKA",
    }


    clean_text = text.strip("():;,.!?[]")
    if len(clean_text) < 2:
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

def check_if_was_defined(blocks, acronyms_with_definitions):

    """ 
    Checks if the acronym was defined before the current block.
    
    Args:
        blocks (list): List of blocks.
        acronyms_with_definitions (dict): Dictionary of acronyms and their definitions.
    
    Returns:
        list: List of error objects.
    """

    matches = []
    for block in blocks.logical_blocks:
        if block.type in {"acronyms", "headings"}:
            continue
        for word in block.words:
            text = word.text
            page = word.page_number
            if not potential_acronym(text):
                continue
            if text in acronyms_with_definitions:
                acronym = acronyms_with_definitions[word.text]
                acronym_page, acronym_bbox = acronym[2], acronym[3]
                if (page, word.bbox[1], word.bbox[0]) < (acronym_page, acronym_bbox[1], acronym_bbox[0]):
                    continue
                else:
                    matches.append(add_match(word, block.block_id))
            else:
                matches.append(add_match(word, block.block_id))

    return matches