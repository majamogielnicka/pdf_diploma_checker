import os
import dataclasses
import json
import morfeusz2

morf = morfeusz2.Morfeusz()

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

def extract_errors_to_json(matches):

    """
    Extracts errors from the list of matches and writes them to a JSON file.
    
    Args:
        matches (list): A list of errors to be extracted.

    Returns:
        None    
    """
    all_matches = []
    for match in matches:
        all_matches.append(dataclasses.asdict(match))

    output_path = os.path.join(os.path.dirname(__file__), "errors.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, ensure_ascii=False, indent=4)