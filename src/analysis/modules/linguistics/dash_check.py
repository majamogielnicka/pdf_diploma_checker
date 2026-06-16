import re
from .linguistics_types import Error_type
from .helpers import get_match_info

def dash_check(blocks):
    '''Checks text blocks for correct usage of hyphens, en dashes and em dashes in Polish and English.'''
    checked_matches = []

    for block in blocks:
        if block.block.type in {"keywords", "math", "code_snippet"}:
            continue
        if block.block.type == "list":
            if block.block.is_bibliography:
                continue
        # Przygotowujemy jednostki do sprawdzenia (tekst + obiekt)
        text = block.contents
        unit = block.block
        text_language = block.language

        errors = []

        has_en_dash = bool(re.search(r'–', text))
        has_em_dash = bool(re.search(r'—', text))

        if unit.type in {"acronyms", "toc", "tof", "tot"}:
            for word in unit.words:
                if word.text == '-':
                    if block.block.language == 'en':
                        message = "Hyphen instead of en dash in a definition."
                    else:
                        message = "Dywiz zamiast półpauzy w definicji."
                    errors.append(Error_type(
                        content='-',
                        category="PUNCTUATION",
                        message=message,
                        offset=word.start_char,
                        error_length=1,
                        block_id=unit.block_id,
                        page_start=word.page_number,
                        page_end=word.page_number,
                        word_idxs=[word.word_index],
                        error_coordinate=[{"page": word.page_number, "coordinates": list(word.bbox)}]
                    ))

        else:
            #" - " lub " -" lub "- "
            hyphen_space_regex = r'(\s-\s|\s-(?=\D|$)|-\s)'
            for m in re.finditer(hyphen_space_regex, text):
                if unit.type == "heading":
                    pos_before = m.start() - 1
                    pos_after = m.end()
                    if (pos_before >= 0 and text[pos_before].isalpha() and
                            pos_after < len(text) and text[pos_after].isalpha()):
                        continue
                start_page, end_page, word_idxs, error_coordinare = get_match_info(unit, m.start(), len(m.group()))
                if block.block.language == 'en':
                    message = "Hyphen instead of en dash or spaces around the hyphen in a hyphenated name."
                else:
                    message = "Dywiz zamiast półpauzy lub spacje wokół dywizu w nazwie łączonej."
                errors.append(Error_type(
                    content=m.group(),
                    category="PUNCTUATION",
                    message= message,
                    offset=m.start(),
                    error_length=len(m.group()),
                    block_id=unit.block_id,
                    page_start=start_page,
                    page_end=end_page,
                    word_idxs=word_idxs,
                    error_coordinate= error_coordinare
                ))

        if has_en_dash and has_em_dash:
            # blad spojnosci jak raz sie uzwa tego i tego
            match = re.search(r'—', text)
            if match:
                start_page, end_page, word_idxs, error_coordinare = get_match_info(unit, match.start(), 1)
                if block.block.language == 'en':
                    message = "Inconsistency: the text uses both en dashes and em dashes."
                else:
                    message = "Niekonsekwencja: w tekście użyto zarówno półpauz, jak i pauz."
                errors.append(Error_type(
                    content="– / —",
                    category="PUNCTUATION",
                    message= message,
                    offset=match.start(),
                    error_length=1,
                    block_id=unit.block_id,
                    page_start=start_page,
                    page_end=end_page,
                    word_idxs=word_idxs,
                    error_coordinate= error_coordinare
                ))

        #litera, myślnik i litera bez spacji
        dash_no_space_regex = r'([a-zA-Z\d])[–—]([a-zA-Z])|([a-zA-Z])[–—]([a-zA-Z\d])'
        for m in re.finditer(dash_no_space_regex, text):
            # Sprawdzamy czy to nie jest zakres dat (cyfra-cyfra), co jest dopuszczalne
            if not (re.match(r'\d', m.group(1) or "") and re.match(r'\d', m.group(2) or "")):
                start_page, end_page, word_idxs, error_coordinare = get_match_info(unit, m.start(), len(m.group()))
                if block.block.language == 'en':
                    message = "Missing space around dash in interjection."
                else:
                    message = "Brak spacji wokół myślnika we wtrąceniu."
                errors.append(Error_type(
                    content=m.group(),
                    category="PUNCTUATION",
                    message=message,
                    offset=m.start(),
                    error_length=len(m.group()),
                    block_id=unit.block_id,
                    page_start=start_page,
                    page_end=end_page,
                    word_idxs=word_idxs,
                    error_coordinate= error_coordinare
                ))

        #daty i zakresy
        if text_language == 'en':
            # en: półpauza bez spacji (1990–2000).
            date_error_regex = r'(\d+\s*[–-]\s*\d+|\d+-\d+)'
            for m in re.finditer(date_error_regex, text):
                content = m.group()
                if '-' in content or ' ' in content:
                    start_page, end_page, word_idxs, error_coordinare = get_match_info(unit, m.start(), len(content))
                    if block.block.language == 'en':
                        message = "English dates do not use spaces around en dashes (–)."
                    else:
                        message = "W angielskich datach nie używa się spacji wokół półpauzy (–)."
                    errors.append(Error_type(
                        content=content,
                        category="PUNCTUATION",
                        message=message,
                        offset=m.start(),
                        error_length=len(content),
                        block_id=unit.block_id,
                        page_start=start_page,
                        page_end=end_page,
                        word_idxs=word_idxs,
                        error_coordinate= error_coordinare
                    ))
        else:
            # pl: półpauza lub dywiz bez spacji (1990–2000 lub 1990-2000).
            date_space_regex = r'(\d+\s+[–-]\s+\d+)'
            for m in re.finditer(date_space_regex, text):
                start_page, end_page, word_idxs, error_coordinare = get_match_info(unit, m.start(), len(m.group()))
                if block.block.language == 'en':
                    message = "In Polish date/number ranges, no spaces are used around the dash."
                else:
                    message = "W polskich zakresach dat/liczb nie używa się spacji wokół myślnika."     
                errors.append(Error_type(
                    content=m.group(),
                    category="PUNCTUATION",
                    message=message,
                    offset=m.start(),
                    error_length=len(m.group()),
                    block_id=unit.block_id,
                    page_start=start_page,
                    page_end=end_page,
                    word_idxs=word_idxs,
                    error_coordinate= error_coordinare
                ))
            

        checked_matches.extend(errors)

    return checked_matches
