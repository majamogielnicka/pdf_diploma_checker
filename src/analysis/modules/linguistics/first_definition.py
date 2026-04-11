import re

def check_first_definition(document):
    """
    Extracts the first definition of an acronym from the document.
    
    Args:
        document (FinalDocument): Parsed JSON document.
    
    Returns:
        list: A list of tuples containing acronyms and their definitions.
    """
    acronyms_with_definitions = []
    for block in document.logical_blocks:
        if block.type == "acronyms":
            list_of_acronyms = re.split("\n", block.content)
            for item in list_of_acronyms:
                defined_acronym = re.split("\s[-–—]\s|\s", item, 1)
                if len(defined_acronym) >= 2:
                    acronyms_with_definitions.append((defined_acronym[0].strip(), defined_acronym[1].strip()))
                else:
                    continue
    return acronyms_with_definitions