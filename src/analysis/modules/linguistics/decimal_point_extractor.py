'''
Sprawdzanie poprawności zapisu dziesiętnego dla języka polskiego i angielskiego.
'''
import re
from .linguistics_types import Error_type
from .helpers import get_match_info
from .exeptions_check import check_quotes
from .proper_check import check_if_proper

def decimal_check(blocks, chapter_nums):
    counter = 0
    checked_matches = []
    chapter_numbers = set()
    for block in blocks:
        if block.block.type in {"math", "code_snippet", "toc", "tot", "tof", "acronyms"}:
            continue
        if block.block.type == "list":
            if block.block.is_bibliography == True:
                continue
        if block.language == 'pl':
            regex = r'(?<![\d.a-zA-Z])\d+\.\d+(?!\.?\d)'
        else:
            regex = r'(\d+,(?!\d{3}(?!\d))\d+)'
        potential_matches = []
        text = block.contents
        regexes = list(re.finditer(regex, text))
        for reg in regexes:
            start_page, end_page, word_idxs, error_coordinate = get_match_info(block.block, reg.start(), reg.end()- reg.start())
            potential_matches.append(Error_type(
                content=text[reg.start():reg.end()],
                category= "DECIMAL",
                message= "",
                offset= reg.start(),
                error_length=reg.end() - reg.start(),
                block_id = block.block.block_id,
                page_start = start_page,
                page_end = end_page,
                word_idxs = word_idxs,
                error_coordinate= error_coordinate,
            ))
        if block.block.type == 'paragraph':
            checked_match, decimal_counter = check_decimal_matches(potential_matches, block, chapter_numbers, 1, chapter_nums)
            checked_matches.extend(checked_match)
        else:
            checked_match, decimal_counter = check_decimal_matches(potential_matches, block, chapter_numbers, 2, chapter_nums)
            checked_matches.extend(checked_match)
        counter += decimal_counter

    return checked_matches, counter

def check_decimal_matches(potential_matches, block, chapter_numbers, error_tolerance, chapter_nums):
    decimal_counter = 0
    black_list = {"%", "$", "€", "£", "zł", "usd", "eur", "gbp", "°"}
    white_list_pl = {"wersja", "wersji", "wersjom", "wersjach", "wersję", "wer","wersją", "wersje", "wersjami", "rys", "rysunek", "rysunkom", "rysunkach", "rysunku", "tabela", "tabele", "tabelę", "tabeli", "tabelom", "tabelach", "tab",
                     "wykres", "wykresu", "wykresom", "wykresowi", "wykresem", "wykresie", "wykresach", "wyk", "rozdziale", "rozdział", "rozdziały", "rozdziału", "rozdziałem", "rozdziałach", "roz", "rozdz", "rozdziałów", 
                     "obraz", "obr", "obrazie", "obrazu", "obrazowi", "obrazach", "obrazem","obrazom", 
                     "wzór", "wzoru", "wzorowi", "wzory", "wzorom", "wzorach", "wzorami", "wzorem", "wzorze"
                     "równanie", "równaniu", "równaniach", "równaniami", "równaniom", "równania", "równaniem", "rów", "listing"}
    checked_matches = []
    for match in potential_matches: 
        is_error = 1 #0 - brak błędu, 1 - potencjalny błąd, 1 - potencjalny błąd, 2 - pewny błąd.
        match_end = match.offset + match.error_length
        after_text = block.contents[match_end:].lstrip()
        before_text = block.contents[:match.offset].rstrip()
        if re.match(r'[^.\d]*\.[ .]{4,}', block.contents):
            chapter_numbers.add(match.content)
            continue 
        if match.content in chapter_numbers:
            continue
        if (before_text.endswith('[') or before_text.endswith('(')) and (after_text.startswith(']') or after_text.startswith(')')):
            continue
        end_check_idx = min(match_end+30, len(block.contents))
        following_text = re.findall(r'[^.()\[\]{}:,;\s]+',block.contents[match_end:end_check_idx].lower())
        begin_check_idx = max(match.offset-30, 0)
        previous_text = re.findall(r'[^.()\[\]{}:,;\s]+', block.contents[begin_check_idx:match.offset].lower())
        if check_quotes(match.offset, match.offset + match.error_length, block.contents):
            is_error = 0
        elif check_if_proper(block.block, match, is_diff= True):
            is_error = 0
        elif following_text and len(set(black_list).intersection(following_text)) > 0:
            is_error = 2
        elif previous_text and len(set(white_list_pl).intersection(previous_text)) > 0:
            is_error = 0
            chapter_numbers.add(match.content)
        elif following_text and len(set(white_list_pl).intersection(following_text)) > 0:
            is_error = 0 
            chapter_numbers.add(match.content)
        elif block.block.type == "heading" and match.word_idxs and (match.word_idxs[0] == 0 or match.word_idxs[0] == 1):
            is_error = 0
        if match.content.strip(" .:,") in chapter_nums and is_error<2:
            is_error = 0
        if is_error>= error_tolerance:
            if is_error == 2:
                error_message = "Niepoprawny separator dziesiętny"
            else:
                error_message = "Możliwe zastosowanie błędnego separatora dziesiętnego"

            match.message = error_message
            decimal_counter = decimal_counter + 1
            checked_matches.append(match)
    return checked_matches, decimal_counter