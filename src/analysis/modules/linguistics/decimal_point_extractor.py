import re
from .linguistics_types import Error_type
from src.analysis.extraction.schema import ParagraphBlock, ListBlock
from .helpers import get_match_info
from .exeptions_check import check_quotes

def decimal_check(text_language, blocks):
    """
    Reads a string and finds decimal numbers with potentially wrong use of decimal points, depending on the language standard.
    Potential errors to be later analysed.
    
    Args:
        blocks (FinalDocument): A list of blocks type logical_blocks
        text_language (str): pl for Polish or en for English to determine which standard should be checked.
    
    Returns:
        list: The list of matches and the text content.
    """
    counter = 0
    checked_matches = []
    if text_language == 'pl':
        regex = r'(?<![\d.a-zA-Z])\d+\.\d+(?!\.?\d)'
    else:
        regex = r'(\d+,(?!\d{3}(?!\d))\d+)'

    for block in blocks.logical_blocks:
        potential_matches = []
        if isinstance(block, ParagraphBlock):
            text = block.content
        elif isinstance(block, ListBlock):
            text = " ".join(item.text for item in block.items if item.text)
        else:
            continue
        regexes = list(re.finditer(regex, text))
        for reg in regexes:
            start_page, end_page, word_idxs = get_match_info(block, reg.start(), reg.end()- reg.start())
            potential_matches.append(Error_type(
                content=text[reg.start():reg.end()],
                category= "DECIMAL",
                message= "",
                offset= reg.start(),
                error_length=reg.end() - reg.start(),
                block_id = block.block_id,
                page_start = start_page,
                page_end = end_page,
                word_idxs = word_idxs,
            ))
        checked_match, decimal_counter = check_decimal_matches(potential_matches, block)
        checked_matches.extend(checked_match)
        counter += decimal_counter
    return checked_matches, counter

def check_decimal_matches(potential_matches, block):

    """
    Checks potentially wrongly used decimal point with criteria.

    Args:
        potential_matches (list): all matches found by initial decimal check.
        text (str): The string of text to be analysed.
    
    Returns:
        tuple[list, str]: A tuple containing the list of matches and the text content. 
    """
    decimal_counter = 0
    text = block.content
    black_list = {"%", "$", "€", "£", "zł", "usd", "eur", "gbp", "°"}
    #for now set with declensions, it's faster than using spacy.
    #once all headers and footers will be extracted, list of chapters and attachments
    white_list_pl = {"wersja", "wersji", "wersjom", "wersjach", "wersję", "wer","wersją", "wersje", "wersjami", "rys", "rysunek", "rysunkom", "rysunkach", "tabela", "tabeli", "tabelom", "wykres", "wykresu", "wykresom", "wykresowi", "wykresie", "wykresach", "rozdziale", "rozdział", "rozdziały", "rozdziałów"}
    checked_matches = []
    for match in potential_matches: 
        is_error = 1 #zero for excluded, 1 for supposed but can not be fully certain, 2 for certain mistake.
        match_end = match.offset + match.error_length
        end_check_idx = min(match_end+30, len(text))
        following_text = re.findall(r'[^.()\[\]{}:,;\s]+',text[match_end:end_check_idx].lower())
        begin_check_idx = max(match.offset-30, 0)
        previous_text = re.findall(r'[^.()\[\]{}:,;\s]+', text[begin_check_idx:match.offset].lower())
        if check_quotes(match, text):
            is_error = 0
        elif following_text and len(set(black_list).intersection(following_text)) > 0:
            is_error = 2
        elif previous_text and len(set(white_list_pl).intersection(previous_text)) > 0:
            is_error = 0
        elif following_text and len(set(white_list_pl).intersection(following_text)) > 0:
            is_error = 0 
        elif block.type == "heading" and match.word_idxs and (match.word_idxs[0] == 0 or match.word_idxs[0] == 1):
            is_error = 0

        if is_error>0:
            if is_error == 2:
                error_message = "Niepoprawny separator dziesiętny"
            else:
                error_message = "Możliwe zastosowanie błędnego separatora dziesiętnego"

            match.message = error_message
            decimal_counter = decimal_counter + 1
            checked_matches.append(match)
    return checked_matches, decimal_counter