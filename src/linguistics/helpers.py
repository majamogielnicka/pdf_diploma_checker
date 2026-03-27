def get_match_info(block, offset, length):
    '''
    Extracts match data.
    
    Args:
        offset (int): Number of beginning index of match in the string
        length (int): Length of the match.
        block (logical_block): contains string and metadata of each word
    
    Returns:
        start_page (int): Page number of the beginning of the match
        end_page (int): Page number of the end of the match
        word_index (list): List of word indexes in the match
    '''
    end_offset = offset + length
    word_idxs = []
    start_page = None
    end_page = None

    for word in block.words:
        if word.start_char < end_offset and word.end_char > offset:
            word_idxs.append(word.word_index)
            if start_page is None:
                start_page = word.page_number
            end_page = word.page_number
    return start_page, end_page, word_idxs