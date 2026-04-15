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
        if block.type == "acronyms":
            continue
        for word in block.words:
            text = word.text
            page = word.page_number
            if not text.isupper() and len(text)<2:
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