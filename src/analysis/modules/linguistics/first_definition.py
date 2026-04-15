import re

def check_position_if_new(new_acronym, definition, words, block_id, acronyms_with_definitions, proper_names):
    if any(word in new_acronym or word in definition for word in proper_names):
        if new_acronym.strip() not in acronyms_with_definitions:
            if new_acronym in words:
                word_page = words[new_acronym].page_number
                word_bbox = words[new_acronym].bbox
                acronyms_with_definitions[new_acronym] = (definition, block_id, word_page, word_bbox)
    return acronyms_with_definitions

def check_first_definition(document, proper_names):
    """
    Extracts the first definition of an acronym from the document.
    
    Args:
        document (FinalDocument): Parsed JSON document.
    
    Returns:
        list: A list of tuples containing acronyms and their definitions.
    """
    acronyms_with_definitions = {}
    list_acronyms = re.compile(r'^[A-Z]{2,}\s+[–—\-−:]\s|^((\S+\s){1,4})[–—\-−:]\s')
    paragraph_def_first = re.compile(r'([A-ZÀ-Ž][a-ząćęłńóśźż\w\s]+)\s*\(([A-Z]{2,})\)')
    paragraph_acr_first = re.compile(r'\(([A-Z]{2,})\)\s([A-ZÀ-Ž][a-ząćęłńóśźż\w\s]+)')
    split = re.compile(r"\s[-–—]\s")
    proper = set(p[0] for p in proper_names)
    for block in document.logical_blocks:
        words = {word.text: word for word in block.words}
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
                    if len(new_acronym) > 1:
                        acronyms_with_definitions = check_position_if_new(new_acronym[0], new_acronym[1].strip(), item.words, block.block_id, acronyms_with_definitions, proper)

        elif block.type in ("paragraph", "heading", "list"):
            if '(' in block.content:
                text = block.content
                new_acronyms = paragraph_def_first.findall(text)
                new_acronyms.extend(paragraph_acr_first.findall(text))
                for new_acronym in new_acronyms:
                    acronyms_with_definitions = check_position_if_new(new_acronym[1], new_acronym[0], words, block.block_id, acronyms_with_definitions, proper)

    #print("\nDetected acronyms and their definitions: \n", "\n ".join([f"\t{acronym} - {definition}, {block_id, page, bbox}" for acronym, (definition, block_id, page, bbox) in acronyms_with_definitions.items()]))
    return acronyms_with_definitions