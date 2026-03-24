import re
from linguistics_types import Error_type
from src.redaction.schema import ParagraphBlock
from helpers import get_match_info

def dash_check(text_language, blocks):
    """
    Analizuje bloki tekstu pod kątem poprawności użycia myślników, półpauz i pauz.
    """
    checked_matches = []
    
    for block in blocks.logical_blocks:
        if not isinstance(block, ParagraphBlock):
            continue
            
        text = block.content
        errors_in_block = []

        has_en_dash = bool(re.search(r'–', text))
        has_em_dash = bool(re.search(r'—', text))
        
        if has_en_dash and has_em_dash:
            # blad spojnosci jak raz sie uzwa tego i tego
            match = re.search(r'—', text)
            if match:
                start_page, end_page, word_idxs = get_match_info(block, match.start(), 1)
                errors_in_block.append(Error_type(
                    content="– / —",
                    category="PUNCTUATION",
                    message="Niekonsekwencja: w tekście użyto zarówno półpauz, jak i pauz.",
                    offset=match.start(),
                    error_length=1,
                    block_id=block.block_id,
                    page_start=start_page,
                    page_end=end_page,
                    word_idxs=word_idxs
                ))

        #" - " lub " -" lub "- "
        hyphen_space_regex = r'(\s-\s|\s-|-\s)'
        for m in re.finditer(hyphen_space_regex, text):
            start_page, end_page, word_idxs = get_match_info(block, m.start(), len(m.group()))
            errors_in_block.append(Error_type(
                content=m.group(),
                category="PUNCTUATION",
                message="Błąd: Spacje wokół dywizu.",
                offset=m.start(),
                error_length=len(m.group()),
                block_id=block.block_id,
                page_start=start_page,
                page_end=end_page,
                word_idxs=word_idxs
            ))

        #litera, myślnik i litera bez spacji
        dash_no_space_regex = r'([a-zA-Z\d])[–—]([a-zA-Z])|([a-zA-Z])[–—]([a-zA-Z\d])'
        for m in re.finditer(dash_no_space_regex, text):
            # Sprawdzamy czy to nie jest zakres dat (cyfra-cyfra), co jest dopuszczalne
            if not (re.match(r'\d', m.group(1) or "") and re.match(r'\d', m.group(2) or "")):
                start_page, end_page, word_idxs = get_match_info(block, m.start(), len(m.group()))
                errors_in_block.append(Error_type(
                    content=m.group(),
                    category="PUNCTUATION",
                    message="Brak spacji wokół myślnika we wtrąceniu.",
                    offset=m.start(),
                    error_length=len(m.group()),
                    block_id=block.block_id,
                    page_start=start_page,
                    page_end=end_page,
                    word_idxs=word_idxs
                ))
        #daty i zakresy
        if text_language == 'en':
            # en: półpauza bez spacji (1990–2000).
            date_error_regex = r'(\d+\s*[–-]\s*\d+|\d+-\d+)'
            for m in re.finditer(date_error_regex, text):
                content = m.group()
                if '-' in content or ' ' in content:
                    start_page, end_page, word_idxs = get_match_info(block, m.start(), len(content))
                    errors_in_block.append(Error_type(
                        content=content,
                        category="PUNCTUATION",
                        message="W angielskich datach nie używaspacji wokół się półpauzy (–).",
                        offset=m.start(),
                        error_length=len(content),
                        block_id=block.block_id,
                        page_start=start_page,
                        page_end=end_page,
                        word_idxs=word_idxs
                    ))
        else:
            # pl: półpauza lub dywiz bez spacji (1990–2000 lub 1990-2000).
            date_space_regex = r'(\d+\s+[–-]\s+\d+)'
            for m in re.finditer(date_space_regex, text):
                start_page, end_page, word_idxs = get_match_info(block, m.start(), len(m.group()))
                errors_in_block.append(Error_type(
                    content=m.group(),
                    category="PUNCTUATION",
                    message="W polskich zakresach dat/liczb nie używa się spacji wokół myślnika.",
                    offset=m.start(),
                    error_length=len(m.group()),
                    block_id=block.block_id,
                    page_start=start_page,
                    page_end=end_page,
                    word_idxs=word_idxs
                ))
        
        checked_matches.extend(errors_in_block)

    return checked_matches
