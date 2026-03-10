import re
from linguistics_types import Error_type

def decimal_check(text_language: str, text: str) -> list:

    """
    Reads a string and finds decimal numbers with potentially wrong use of decimal points, depending on the language standard.
    Potential errors to be later analysed.
    
    Args:
        text (str): The string of text to be analysed.
        text_language (str): pl for Polish or en for English to determine which standard should be checked.
    
    Returns:
        list: The list of matches and the text content.
    """

    if text_language == 'pl':
        regex = r'(\d+\.\d+)'
    else:
        regex = r'(\d+\,\d+)'

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
    
    #trying to figure out a way to make this universal without creating a massive amount of false positives.
    black_list = ["%", "$", "€", "£", "zł", "usd", "eur", "gbp"]

    #TODO: adjust this to actual numbers of chapters, listings etc in the document
    white_list = ["rys", "rysunek", "rysunkom", "rysunkach", "tabela", "tabeli", "tabelom"]

    checked_matches = []
    for match in potential_matches:
        is_error = 1 #zero for excluded, 1 for supposed but can not be fully certain, 2 for certain mistake.
        end_check_idx = min(match.end()+30, len(text))
        following_text = text[match.end():end_check_idx].lower().split()
        if following_text and len(set(black_list).intersection(following_text)) > 0:
            is_error = 2
        #TODO: exclude numbers with certain structers such as dates, IP adresses.
        begin_check_idx = max(match.start()-30, 0)
        previous_text = text[begin_check_idx:match.start()].lower().split()
        if previous_text and len(set(white_list).intersection(previous_text)) > 0:
            is_error = 0
        if following_text and len(set(white_list).intersection(following_text)) > 0:
            is_error = 0 
        
        if is_error>0:
            if is_error == 2:
                error_message = "Niepoprawny separator dziesiętny"
            else:
                error_message =  "Możliwe zastosowanie błędnego separatora dziesiętnego"

            checked_match = Error_type(
                category = "Separator dziesiętny",
                message = error_message,
                offset = match.start(),
                error_length = match.end() - match.start()
            )

            checked_matches.append(checked_match)

    return checked_matches