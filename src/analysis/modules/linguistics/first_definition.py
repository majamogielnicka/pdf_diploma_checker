import re
from .check_acronym import potential_acronym

def check_position_if_new(new_acronym, definition, words, block_id, acronyms_with_definitions, proper_names):

    TITLE_PAGE_PHRASES = {
    "PRACA", "MAGISTERSKA", "INŻYNIERSKA", "DYPLOMOWA",
    "STRESZCZENIE", "ABSTRACT", "SŁOWA", "KLUCZOWE",
    "KEYWORDS", "WYKAZ", "SKRÓTÓW", "ABBREVIATIONS",
    "ENGINEERING", "THESIS", "UNIVERSITY", "POLITECHNIKA",
    }
    new_acronym_clean = new_acronym.strip()
    if new_acronym_clean not in acronyms_with_definitions:
        if new_acronym_clean in TITLE_PAGE_PHRASES:
            return acronyms_with_definitions
            
        words_list = list(words.values()) if isinstance(words, dict) else words
        word_page, word_bbox = None, None
        
        for w in words_list:
            if w.text == new_acronym_clean:
                word_page = w.page_number
                word_bbox = w.bbox
                break
                
        if word_page is None:
            for w in words_list:
                if w.text.startswith(new_acronym_clean):
                    word_page = w.page_number
                    word_bbox = w.bbox
                    break
        
        if word_page is None and len(words_list) > 0:
            w = words_list[0]
            word_page = w.page_number
            word_bbox = w.bbox
            
        if word_page is not None and word_page > 1:
            acronyms_with_definitions[new_acronym_clean] = (definition, block_id, word_page, word_bbox)
            
    return acronyms_with_definitions

def check_first_definition(blocks, proper_names):
    """
    Extracts the first definition of an acronym from the document.
    
    Args:
        document (FinalDocument): Parsed JSON document.
    
    Returns:
        list: A list of tuples containing acronyms and their definitions.
    """

    acronyms_with_definitions = {}
    list_acronyms = re.compile(r'^[A-Z]{2,}\s+[\u2013\u2014\-\u2212:]\s|^((\S+\s){1,4})[\u2013\u2014\-\u2212:]\s')
    paragraph_def_first = re.compile(r'([A-Z\u00c0-\u017d][a-z\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c\w\s]+)\s*\(([A-Z]{2,})\)')
    paragraph_acr_first = re.compile(r'\(([A-Z]{2,})\)\s([A-Z\u00c0-\u017d][a-z\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c\w\s]+)')
    paragraph_acr_then_expansion = re.compile(r'\b([A-Z]{2,})\s*\(([A-Z][a-zA-ZÀ-Ž][a-zA-ZÀ-Žąćęłńóśźż\s\-]{2,})\)')
    split = re.compile(r"\s[-\u2013\u2014]\s")
    proper = set(p[0] for p in proper_names)
    for block in blocks:
        block = block.block
        words = block.words
        if block.type == "acronyms":
            list_of_acronyms = block.content.split("\n")
            for item in list_of_acronyms:
                defined_acronym = split.split(item, 1)
                if len(defined_acronym) >= 2:
                    acronyms_with_definitions = check_position_if_new(defined_acronym[0], defined_acronym[1], words, block.block_id, acronyms_with_definitions, proper)
                else:
                    continue
        elif block.type == "list":
            for item in block.items:
                if list_acronyms.search(item.text):
                    new_acronym = split.split(item.text, 1)
                    new_acronym[0] = new_acronym[0].strip()
                    if len(new_acronym) > 1 and potential_acronym(new_acronym[0]):
                        acronyms_with_definitions = check_position_if_new(new_acronym[0], new_acronym[1].strip(), item.words, block.block_id, acronyms_with_definitions, proper)

        if block.type in ("paragraph", "heading", "list"):
            if '(' in block.content:
                text = block.content
                new_acronyms = paragraph_acr_first.findall(text)
                new_acronyms.extend(paragraph_acr_then_expansion.findall(text))
                for new_acronym in new_acronyms:
                    acronyms_with_definitions = check_position_if_new(new_acronym[0], new_acronym[1], words, block.block_id, acronyms_with_definitions, proper)
                new_acronyms = paragraph_def_first.findall(text)
                for new_acronym in new_acronyms:
                    acronyms_with_definitions = check_position_if_new(new_acronym[1], new_acronym[0], words, block.block_id, acronyms_with_definitions, proper)
    return acronyms_with_definitions