from .helpers import add_match, get_match_info
import re
from collections import Counter 

def get_item_offset(block, target_item_id):
    offset = 0
    for it in block.items:
        if it.item_id == target_item_id:
            return offset
        offset += len(it.text) + 1
    return 0


def check_order(block, matches, item):
    
    EXPECTED_ORDER = {
    "article":       ["authors", "title", "journal", "volume", "date", "pages"],
    "book":          ["authors", "title", "publisher", "date"],
    "inbook":        ["authors", "title", "publisher", "date", "pages"],
    "incollection":  ["authors", "title", "book_title", "publisher", "date", "pages"],
    "inproceedings": ["authors", "title", "book_title", "date"],
    "online":        ["authors", "title", "url", "access_date"],
    "thesis":        ["authors", "title", "publisher", "date"],
    None:            ["authors", "title", "publisher", "date"],
    }

    Category_and_message = {
        "WRONG_ORDER_ISO": "Wpis w bibliografii jest w złej kolejności.",
    }
    text = item.content
    positions = {}

    if item.authors: positions['authors'] = text.find(item.authors)
    if item.title: positions['title'] = text.find(item.title)
    if item.date: positions['date'] = text.find(item.date)
    if item.journal: positions['journal'] = text.find(item.journal)
    if item.volume: positions['volume'] = text.find(item.volume)
    if item.pages: positions['pages'] = text.find(item.pages)
    if item.url: positions['url'] = text.find(item.url)
    if item.access_date: positions['access_date'] = text.find(item.access_date)
    if item.book_title: positions['book_title'] = text.find(item.book_title)
    if item.publisher:
        positions['publisher'] = text.find(item.publisher)

    positions = {k: v for k, v in positions.items() if v != -1}
    
    if not positions:
        return matches

    actual_order = sorted(positions.keys(), key=lambda k: positions[k])
    expected_order = EXPECTED_ORDER.get(item.entry_type, EXPECTED_ORDER[None])
    expected_present = [elem for elem in expected_order if elem in actual_order]
    
    actual_filtered = [k for k in actual_order if k in expected_present]
    if actual_filtered != expected_present:
        item_off = get_item_offset(block, item.item.item_id)
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(text))
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "WRONG_ORDER_ISO", Category_and_message["WRONG_ORDER_ISO"]))

    return matches

def get_field_separator(item):

    text = item.content
    known_fields = []

    for field in ['authors', 'title', 'book_title', 'journal', 'publisher', 'date', 'pages', 'volume']:
        val = getattr(item, field, None)
        if val:
            pos = text.find(val)
            if pos != -1:
                known_fields.append((pos, pos + len(val)))

    known_fields.sort(key=lambda x: x[0])
    separators = []

    for i in range(len(known_fields) - 1):

        end_prev  = known_fields[i][1]
        start_next = known_fields[i + 1][0]
        between = text[end_prev:start_next].strip()
        sep = re.match(r'^[.,;]', between)
        if sep:
            separators.append(sep.group(0))

    return Counter(separators).most_common()[0][0] if separators else None

def check_iso(matches, item, block):

    Category_and_message = {
        "MISSING_FINAL_DOT": "Nie zastosowano kropki na końcu wpisu.",
        "SEPARATOR_COHERENCE": "Separatory nie są spójne wewnątrz wpisu."
    }
    separator = re.compile(r'[;,.]')
    text = item.content.strip()
    ends_with_url = bool(re.search(r'https?://\S+$|www\.\S+$|doi\.org/\S+$', text))
    if not text.endswith('.') and not ends_with_url:
        item_off = get_item_offset(block, item.item.item_id)
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_FINAL_DOT", Category_and_message["MISSING_FINAL_DOT"]))

    if item.authors:
        separators = separator.findall(text)
        authors_separator = separator.findall(item.authors)

        if separators:
            item.separator = get_field_separator(item)

        if authors_separator and separators:
            dominant_author_separator = Counter(authors_separator).most_common()[0][0]
            dominant_separator = Counter(separators).most_common()[0][0]
            if dominant_separator != dominant_author_separator:
                item.separator = dominant_separator
    
    check_order(block, matches, item)

    return matches

def add_bibtex_type(Bib_context):
    
    for item in Bib_context.items:
        if item.online or item.url:
            item.bibtex_type = "online"
        elif re.search("rozprawa|thesis|Uniwersytet|Politechnika|University", item.content):
            item.bibtex_type = "thesis"
        elif item.journal:
            item.bibtex_type = "article"
        elif item.publisher and item.book_title:
            item.bibtex_type = "incollection"
        elif item.publisher and item.pages and item.is_title_italics:
            item.bibtex_type = "inbook"
        elif item.book_title:
            item.bibtex_type = "inproceedings"
        elif item.publisher and not item.journal:
            item.bibtex_type = "book"
        else:
            item.bibtex_type = "misc"

def check_bibtex(matches, Bib_context, bib_blocks):
    
    Category_and_message = {
        "WRONG_BIBTEX_TYPE": "Nie udało się sklasyfikować wpisu w bibliografii.",
        "MISSING_BIBTEX_FIELD": "Brakuje wymaganego pola dla tego typu wpisu BibTeX.",
        "BIBTEX_ONLINE_NO_ACCESS_DATE": "Wpis typu @online w BibTeX powinien zawierać datę dostępu (urldate).",
        "BIBTEX_URL_NO_ACCESS_DATE": "Wpis zawiera URL, ale brak daty dostępu (urldate) — wymagane w BibTeX.",
    }
    required_fields_per_type = {
        "article": ["authors", "title", "journal", "date"],
        "book": ["authors", "title", "publisher", "date"],
        "inbook": ["authors", "title", "publisher", "date", "pages"],
        "incollection": ["authors", "title", "book_title", "publisher", "date"],
        "inproceedings": ["authors", "title", "book_title", "date"],
        "online": ["title", "url"], 
        "thesis": ["authors", "title", "date"] 
    }

    add_bibtex_type(Bib_context)
    for item in Bib_context.items:
        block = bib_blocks.get(item.item.item_id)
        if block is None:
            continue
        if item.bibtex_type is None:
            item_off = get_item_offset(block, item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
            matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "WRONG_BIBTEX_TYPE",Category_and_message["WRONG_BIBTEX_TYPE"]))
            continue  

        required = required_fields_per_type.get(item.bibtex_type, [])
        missing = [f for f in required if not getattr(item, f, None)]
        if missing:
            msg = f"{Category_and_message['MISSING_BIBTEX_FIELD']} ({item.bibtex_type}: {', '.join(missing)})"
            item_off = get_item_offset(block, item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
            matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx,error_coordinate, "MISSING_BIBTEX_FIELD", msg))

        if item.bibtex_type == "online" and not item.access_date:
            item_off = get_item_offset(block, item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
            matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "BIBTEX_ONLINE_NO_ACCESS_DATE", Category_and_message["BIBTEX_ONLINE_NO_ACCESS_DATE"]))

        if item.url and not item.access_date and item.bibtex_type != "online":
            item_off = get_item_offset(block, item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
            matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "BIBTEX_URL_NO_ACCESS_DATE", Category_and_message["BIBTEX_URL_NO_ACCESS_DATE"]))

    return matches

def check_item(matches, item, block):

    Category_and_message = {
        "MISSING_OBLIGATORY": "Brakuje autorów, tytułu lub daty.",
        "MISSING_PUBLISHER": "Brakuje wydawcy dla pozycji książkowej.",
        "MISSING_ONLINE": "Brakuje pól obowiązkowych dla prac online.",
        "MISSING_JOURNAL": "Brakuje stron dla artykułu.",
        "URL_NO_ACCESS_DATE": "Wpis zawiera URL, ale brak daty dostępu.",
        "ACCESS_DATE_NO_URL": "Wpis zawiera datę dostępu, ale brak URL/DOI.",
    }
    text = item.content.strip()
    if item.authors is None or item.title is None or item.date is None:
        item_off = get_item_offset(block, item.item.item_id)
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_OBLIGATORY", Category_and_message["MISSING_OBLIGATORY"]))

    if item.entry_type in ["book", "incollection"] and item.publisher is None:
        item_off = get_item_offset(block, item.item.item_id)
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_PUBLISHER", Category_and_message["MISSING_PUBLISHER"]))

    if item.online:
        if not item.access_date:
            item_off = get_item_offset(block, item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
            matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_ONLINE", Category_and_message["MISSING_ONLINE"]))
        if not item.url and not item.doi:
            item_off = get_item_offset(block, item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
            matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_ONLINE", Category_and_message["MISSING_ONLINE"]))

    if item.journal and not item.pages:
        item_off = get_item_offset(block, item.item.item_id)
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_JOURNAL", Category_and_message["MISSING_JOURNAL"]))

    if item.url and not item.access_date and not item.online:
        item_off = get_item_offset(block, item.item.item_id)
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "URL_NO_ACCESS_DATE", Category_and_message["URL_NO_ACCESS_DATE"]))

    if item.access_date and not item.url and not item.doi:
        item_off = get_item_offset(block, item.item.item_id)
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "ACCESS_DATE_NO_URL", Category_and_message["ACCESS_DATE_NO_URL"]))
    
    return matches

def check_coherence_iso(matches, Bib_context, bib_blocks):

    Category_and_message = {
        "SEPARATOR_COHERENCE": "Niespójna forma separatora we wpisach w bibliografii.",
        "AUTHOR_FORMAT_COHERENCE": "Niespójny format autorów we wpisach w bibliografii.",
        "DATE_FORMAT_COHERENCE": "Niespójny format dat we wpisach w bibliografii.",
        "TITLE_FORMAT_COHERENCE": "Niespójny format tytułów we wpisach w bibliografii (kursywa vs cudzysłów).",
        "MULTI_AUTHOR_SEP_COHERENCE": "Niespójny sposób oddzielania wielu autorów (np. 'and' vs 'i' vs ',').",
        "DATE_POSITION_COHERENCE": "Niespójna pozycja daty we wpisach (na początku vs na końcu).",
        "MARKER_TYPE_COHERENCE": "Niespójny typ markera (numeracji) we wpisach bibliografii.",
    }

    separators, author_formats = [], []
    date_formats, title_formats = [], []
    multi_author_seps, date_positions = [], []
    marker_types = []

    for item in Bib_context.items:
        block = bib_blocks.get(item.item.item_id)
        if block is None:
            continue
        check_item(matches, item, block)
        check_iso(matches, item, block)
        if item.separator:
            separators.append(item.separator)
        if item.author_format:
            author_formats.append(item.author_format)
        if item.date_format:
            date_formats.append(item.date_format)
        if item.multi_author_sep:
            multi_author_seps.append(item.multi_author_sep)
        if item.date_position:
            date_positions.append(item.date_position)

        if item.has_italic and item.has_quotes:
            title_formats.append('italic+quotes')
        elif item.is_title_italics:
            title_formats.append('italic')
        elif item.has_quotes:
            title_formats.append('quotes')
        elif item.has_bold:
            title_formats.append('bold')

        if hasattr(item, 'item') and hasattr(item.item, 'marker_type') and item.item.marker_type:
            marker_types.append(item.item.marker_type)

    if separators:
        Bib_context.dominant_separator = Counter(separators).most_common()[0][0]
    if author_formats:
        Bib_context.dominant_author_format = Counter(author_formats).most_common()[0][0]
    if date_formats:
        Bib_context.dominant_date_format = Counter(date_formats).most_common()[0][0]
    if multi_author_seps:
        Bib_context.dominant_multi_author_sep = Counter(multi_author_seps).most_common()[0][0]
    if date_positions:
        Bib_context.dominant_date_position = Counter(date_positions).most_common()[0][0]
    if marker_types:
        Bib_context.dominant_marker_type = Counter(marker_types).most_common()[0][0]

    title_base_formats = []
    for tf in title_formats:
        if tf == 'italic+quotes':
            title_base_formats.append('quotes')
        else:
            title_base_formats.append(tf)
    if title_base_formats:
        Bib_context.dominant_title_format = Counter(title_base_formats).most_common()[0][0]

    for item in Bib_context.items:
        block = bib_blocks.get(item.item.item_id)
        if block is None:
            continue

        if item.separator and item.separator != Bib_context.dominant_separator:
            item_off = get_item_offset(block, item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
            matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "SEPARATOR_COHERENCE", Category_and_message["SEPARATOR_COHERENCE"]))

        if item.author_format and item.author_format != Bib_context.dominant_author_format:
            item_off = get_item_offset(block, item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
            matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "AUTHOR_FORMAT_COHERENCE", Category_and_message["AUTHOR_FORMAT_COHERENCE"]))

        if item.date_format and Bib_context.dominant_date_format:
            if item.date_format != Bib_context.dominant_date_format:
                item_off = get_item_offset(block, item.item.item_id)
                p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
                matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "DATE_FORMAT_COHERENCE", Category_and_message["DATE_FORMAT_COHERENCE"]))

        if Bib_context.dominant_title_format:
            item_title_fmt = None
            if item.has_italic and item.has_quotes:
                item_title_fmt = 'quotes'
            elif item.is_title_italics:
                item_title_fmt = 'italic'
            elif item.has_quotes:
                item_title_fmt = 'quotes'
            elif item.has_bold:
                item_title_fmt = 'bold'

            if item_title_fmt and item.entry_type not in ('article', 'incollection'):
                if item_title_fmt != Bib_context.dominant_title_format:
                    item_off = get_item_offset(block, item.item.item_id)
                    p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
                    matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "TITLE_FORMAT_COHERENCE", Category_and_message["TITLE_FORMAT_COHERENCE"]))

        if item.multi_author_sep and Bib_context.dominant_multi_author_sep and len(multi_author_seps) >= 3:
            if item.multi_author_sep != Bib_context.dominant_multi_author_sep:
                item_off = get_item_offset(block, item.item.item_id)
                p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
                matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "MULTI_AUTHOR_SEP_COHERENCE", Category_and_message["MULTI_AUTHOR_SEP_COHERENCE"]))

        if item.date_position and Bib_context.dominant_date_position and not item.online:
            if item.date_position != Bib_context.dominant_date_position:
                item_off = get_item_offset(block, item.item.item_id)
                p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
                matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "DATE_POSITION_COHERENCE", Category_and_message["DATE_POSITION_COHERENCE"]))

        if Bib_context.dominant_marker_type:
            item_marker = getattr(item.item, 'marker_type', None)
            if item_marker and item_marker != Bib_context.dominant_marker_type:
                item_off = get_item_offset(block, item.item.item_id)
                p_start, p_end, word_idx, error_coordinate = get_match_info(block, item_off, len(item.content))
                matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "MARKER_TYPE_COHERENCE", Category_and_message["MARKER_TYPE_COHERENCE"]))

    return matches
