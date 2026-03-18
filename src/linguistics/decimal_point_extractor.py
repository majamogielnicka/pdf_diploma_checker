import re
from linguistics_types import Error_type

def decimal_check(text_language: str, text_blocks: list) -> list:

    """
    Reads a string and finds decimal numbers with potentially wrong use of decimal points, depending on the language standard.
    Potential errors to be later analysed.
    
    Args:
        text (list): A list of blocks type ChapterBlocks
        text_language (str): pl for Polish or en for English to determine which standard should be checked.
    
    Returns:
        list: The list of matches and the text content.
    """

    if text_language == 'pl':
        regex = r'(?<![\d.a-zA-Z])\d+\.\d+(?!d|\.\d)'
    else:
        regex = r'(\d+,(?!\d{3}(?!\d))\d+)' 
    #for block in text_blocks:
    #text = block.content
    text = text_blocks
    potential_matches = list(re.finditer(regex, text))
    checked_matches = check_decimal_matches(potential_matches, text)
    return checked_matches


def check_decimal_matches(potential_matches: list[re.Match[str]], text: str) -> list:

    """
    Checks potentially wrongly used decimal point with criteria.

    Args:
        potential_matches (list): all matches found by initial decimal check.
        text (str): The string of text to be analysed.
    
    Returns:
        tuple[list, str]: A tuple containing the list of matches and the text content. 
    """
    black_list = {"%", "$", "€", "£", "zł", "usd", "eur", "gbp"}
    #for now set with declensions, it's faster than using spacy.
    white_list_pl = {"wersja", "wersji", "wersjom", "wersjach", "wersję", "wer","wersją", "wersje", "wersjami", "rys", "rysunek", "rysunkom", "rysunkach", "tabela", "tabeli", "tabelom"}
    #white_list_en = {"version", "versions", "ver", "chart", "charts", "graph", "graphs", "diagram", "diagrams", "scheme", "schemes", "illustration"}
    checked_matches = []
    for match in potential_matches:
        is_error = 1 #zero for excluded, 1 for supposed but can not be fully certain, 2 for certain mistake.
        end_check_idx = min(match.end()+30, len(text))
        following_text = text[match.end():end_check_idx].lower().split()
        if following_text and len(set(black_list).intersection(following_text)) > 0:
            is_error = 2
        begin_check_idx = max(match.start()-30, 0)
        #to be adjusted to extracted 
        previous_text = text[begin_check_idx:match.start()].lower().split()
        if previous_text and len(set(white_list_pl).intersection(previous_text)) > 0:
            is_error = 0
        if following_text and len(set(white_list_pl).intersection(following_text)) > 0:
            is_error = 0 
        #TODO: check font for headers, bold, illiadic, numbers with letters.
        if is_error>0:
            if is_error == 2:
                error_message = "Niepoprawny separator dziesiętny"
            else:
                error_message =  "Możliwe zastosowanie błędnego separatora dziesiętnego"

            checked_match = Error_type(
                content = text[match.start():match.end()],
                category = "Separator dziesiętny",
                message = error_message,
                offset = match.start(),
                error_length = match.end() - match.start()
            )

            checked_matches.append(checked_match)
    return checked_matches