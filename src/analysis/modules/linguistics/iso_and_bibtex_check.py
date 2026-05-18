from .helpers import add_match, get_match_info
import re
from collections import Counter 

def check_item_words(matches, item, block, category, message, content):
    if not item.item.words:
        return matches
    words = item.item.words
    word_idxs = [w.word_index for w in words]
    page_start = words[0].page_number
    page_end = words[-1].page_number
    error_coordinate = [{"page": words[0].page_number, "coordinates": [min(w.bbox[0] for w in words), min(w.bbox[1] for w in words), max(w.bbox[2] for w in words), max(w.bbox[3] for w in words)]}]
    matches.append(add_match(content, block.block_id, page_start, page_end, word_idxs, error_coordinate, category, message))
    return matches

def get_text(field):
    if not field or not isinstance(field, dict):
        return None
    return next(iter(field.keys()), None)

def get_format(field):
    if not field or not isinstance(field, dict):
        return None
    return next(iter(field.values()), None)

def check_order(block, matches, item):
    
    expected_order = {
    "article":       ["authors", "journal", "volume", "date", "pages"],
    "book":          ["authors", "publisher", "date"],
    "inproceedings": ["authors", "date"],
    "online":        ["authors", "url", "access_date"],
    None:            ["authors", "date"],
    }

    Category_and_message = {
        "WRONG_ORDER_ISO": "Wpis w bibliografii jest w złej kolejności.",
    }
    text = item.content
    positions = {}

    if item.authors and get_text(item.authors): positions['authors'] = text.find(get_text(item.authors))
    if item.title and get_text(item.title): positions['title'] = text.find(get_text(item.title))
    if item.date and len(item.date) > 0 and get_text(item.date[0]): positions['date'] = text.find(get_text(item.date[0]))
    if getattr(item, 'journal', None) and get_text(item.journal): positions['journal'] = text.find(get_text(item.journal))
    if item.volume and get_text(item.volume): positions['volume'] = text.find(get_text(item.volume))
    if item.pages and get_text(item.pages): positions['pages'] = text.find(get_text(item.pages))
    if item.url and get_text(item.url): positions['url'] = text.find(get_text(item.url))
    if item.access_date and get_text(item.access_date): positions['access_date'] = text.find(get_text(item.access_date))
    if item.book_title and get_text(item.book_title): positions['book_title'] = text.find(get_text(item.book_title))
    if item.publisher and get_text(item.publisher): positions['publisher'] = text.find(get_text(item.publisher))

    positions = {k: v for k, v in positions.items() if v != -1}
    
    if not positions:
        return matches

    actual_order = sorted(positions.keys(), key=lambda k: positions[k])
    expected_order = expected_order.get(item.bibtex_type, expected_order[None])
    expected_present = [elem for elem in expected_order if elem in actual_order]
    
    actual_filtered = [k for k in actual_order if k in expected_present]
    if actual_filtered != expected_present:
        matches = check_item_words(matches, item, block, "WRONG_ORDER_ISO", Category_and_message["WRONG_ORDER_ISO"], text)

    return matches

def get_field_separator(item):

    text = item.content
    known_fields = []

    for field in ['authors', 'title', 'book_title', 'journal', 'publisher', 'date', 'pages', 'volume']:
        val = getattr(item, field, None)
        if val:
            if isinstance(val, list) and len(val) > 0:
                val_str = get_text(val[0])
            elif isinstance(val, dict):
                val_str = get_text(val)
            else:
                continue

            pos = text.find(val_str)
            if pos != -1:
                known_fields.append((pos, pos + len(val_str)))

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

    # if item.item.marker_type == "number_in_brackets":
    #     return matches

    Category_and_message = {
        "MISSING_FINAL_DOT": "Nie zastosowano kropki na końcu wpisu.",
    }
    separator = re.compile(r'[;,.]')
    text = item.content.strip()
    ends_with_url = bool(re.search(r'https?://\S+$|www\.\S+$|doi\.org/\S+$', text))
    if not text.endswith('.') and not ends_with_url:
        matches = check_item_words(matches, item, block, "MISSING_FINAL_DOT", Category_and_message["MISSING_FINAL_DOT"], text)

    if item.authors and get_text(item.authors):
        separators = separator.findall(text)
        authors_separator = separator.findall(get_text(item.authors))

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
    
    keywords = {
    'proceedings', 'conference', 'symposium', 'workshop', 'congress',
    'konferencja', 'konferencji', 'seminarium', 'international',
    'handbook', 'monograph'
    }

    for item in Bib_context.items:
        has_url         = bool(item.url and get_text(item.url))
        has_access_date = bool(item.access_date and get_text(item.access_date))
        has_pub_date    = bool(item.date and len(item.date) > 0 and get_text(item.date[0]))
        has_journal     = bool(getattr(item, 'journal', None) and get_text(item.journal))
        
        publisher_text = get_text(item.publisher) or ""
        publisher_fmt  = get_format(item.publisher) if item.publisher else None
        publisher_is_journal     = publisher_fmt == 'italic' and not has_url
        publisher_is_proceedings = (
            publisher_is_journal and
            any(kw in publisher_text.lower() for kw in keywords)
        )

        if has_journal or publisher_is_journal:
            item.bibtex_type = "article"
            if not getattr(item, 'journal', None):
                item.journal = item.publisher
                item.publisher = None
        elif publisher_is_proceedings:
            item.bibtex_type = "inproceedings"
            if not getattr(item, 'book_title', None):
                item.book_title = item.publisher
                item.publisher = None
        elif getattr(item, 'online', False) or (has_url and not has_pub_date):
            item.bibtex_type = "online"
            if not getattr(item, 'journal', None):
                item.journal = item.publisher
                item.publisher = None
        elif item.publisher and get_text(item.publisher):
            item.bibtex_type = "book"
        else:
            raw_text = item.content.lower()
            
            if "arxiv" in raw_text or "preprint" in raw_text:
                item.bibtex_type = "article"
            elif any(kw in raw_text for kw in keywords): 
                item.bibtex_type = "inproceedings"
            elif "journal" in raw_text or "transactions" in raw_text or "letters" in raw_text or re.search(r'\d+\(\d+\)', raw_text):
                item.bibtex_type = "article"
            else:
                item.bibtex_type = "None"

def check_bibtex(matches, Bib_context, bib_blocks):
    
    Category_and_message = {
        "WRONG_BIBTEX_TYPE": "Nie udało się sklasyfikować wpisu w bibliografii.",
        "MISSING_BIBTEX_FIELD": "Brakuje wymaganego pola dla tego typu wpisu BibTeX.",
    }
    required_fields_per_type = {
        "article": ["authors", "journal", "date"],
        "book": ["authors", "publisher", "date"],
        "inproceedings": ["authors", "date"],
        "online": ["url"], 
    }

    add_bibtex_type(Bib_context)
    for item in Bib_context.items:
        block = bib_blocks.get(item.item.item_id)
        if block is None:
            continue
        if item.bibtex_type is None:
            matches = check_item_words(matches, item, block, "WRONG_BIBTEX_TYPE",Category_and_message["WRONG_BIBTEX_TYPE"], item.content)
            continue  

        required = required_fields_per_type.get(item.bibtex_type, [])
        missing = []
        for f in required:
            val = getattr(item, f, None)
            if not val:
                missing.append(f)
            elif isinstance(val, dict) and not get_text(val):
                missing.append(f)
            elif isinstance(val, list) and (len(val) == 0 or not get_text(val[0])):
                missing.append(f)
        
        if missing:
            if 'journal' in missing and re.search(r'arxiv|preprint', item.content, re.IGNORECASE):
                missing.remove('journal')

            if missing: 
                msg = f"{Category_and_message['MISSING_BIBTEX_FIELD']} ({item.bibtex_type}: {', '.join(missing)})"
                matches = check_item_words(matches, item, block, "MISSING_BIBTEX_FIELD", msg, item.content)

    return matches

def check_item(matches, item, block):

    Category_and_message = {
        "MISSING_OBLIGATORY": "Brakuje autorów, tytułu lub daty.",
        "MISSING_PUBLISHER": "Brakuje wydawcy dla pozycji książkowej.",
        "MISSING_ONLINE": "Brakuje pól obowiązkowych dla prac online.",
        "MISSING_PAGES": "Brakuje stron dla artykułu.",
        "MISSING_ARTICLE_OR_BOOK": "Brakuje danych identyfikacyjnych pracy.",
        "NO_ACCESS_DATE_OR_DOI": "Brakuje daty dostępu lub doi.",
    }
    text = item.content.strip()
    
    if item.bibtex_type != "online":
        if not get_text(item.authors) or (not item.date or len(item.date) == 0 or not get_text(item.date[0])):
            matches = check_item_words(matches, item, block, "MISSING_OBLIGATORY", Category_and_message["MISSING_OBLIGATORY"], text)
            return matches

    if item.bibtex_type =="book" and (not item.publisher or not get_text(item.publisher)):
        matches = check_item_words(matches, item, block, "MISSING_PUBLISHER", Category_and_message["MISSING_PUBLISHER"], text)

    if item.online:
        if not item.access_date or not get_text(item.access_date):
            matches = check_item_words(matches, item, block, "MISSING_ONLINE", Category_and_message["MISSING_ONLINE"], text)
        if not get_text(item.url) and not get_text(item.doi) and not get_text(item.publisher):
            matches = check_item_words(matches, item, block, "MISSING_ARTICLE_OR_BOOK", Category_and_message["MISSING_ARTICLE_OR_BOOK"], text)

    if getattr(item, 'journal', None) and get_text(item.journal):
        journal_text = get_text(item.journal) or ""
    
        book_keywords = {
            'handbook', 'synthesis', 'monograph', 'textbook',
            'edition', 'podręcznik', 'monografia', 'kompendium'
        }
        is_book_like = (
            len(journal_text) > 60
            or any(kw in journal_text.lower() for kw in book_keywords)
        )
        
        if not is_book_like:
            has_pages_in_context = item.pages and get_text(item.pages)
            has_pages_in_text = re.search(r'\b(?:art(?:icle)?\.?|pp?\.)\s*\d+|\b\d+:\d+\b', text, re.IGNORECASE)
            has_book_volume = bool(re.search(r'\bvolume\s+\d+', text, re.IGNORECASE))
            is_preprint_or_repo = re.search(r'arxiv|preprint|zenodo|biorxiv', text, re.IGNORECASE)

            if not has_pages_in_context and not has_pages_in_text and not has_book_volume and not is_preprint_or_repo:
                matches = check_item_words(matches, item, block, "MISSING_PAGES", Category_and_message["MISSING_PAGES"], text)

    if item.url and get_text(item.url) and not item.doi and (not item.access_date or not get_text(item.access_date)) and not item.online:
        matches = check_item_words(matches, item, block, "NO_ACCESS_DATE_OR_DOI", Category_and_message["NO_ACCESS_DATE_OR_DOI"], text)
    
    return matches

def check_coherence_iso(matches, Bib_context, bib_blocks):

    Category_and_message = {
        "SEPARATOR_COHERENCE": "Niespójna forma separatora we wpisach w bibliografii.",
        "AUTHOR_FORMAT_COHERENCE": "Niespójny format autorów we wpisach w bibliografii.",
        "DATE_FORMAT_COHERENCE": "Niespójny format dat we wpisach w bibliografii.",
        "TITLE_FORMAT_COHERENCE": "Niespójny format tytułów we wpisach w bibliografii.",
        "DATE_POSITION_COHERENCE": "Niespójna pozycja daty we wpisach w bibliografii.",
    }

    add_bibtex_type(Bib_context)
    separators, author_formats = {}, {}
    date_formats, title_formats = {}, {}
    date_positions = {}
    marker_types = []

    for item in Bib_context.items:
        block = bib_blocks.get(item.item.item_id)
        if block is None:
            continue
        check_item(matches, item, block)
        check_iso(matches, item, block)
        t = item.bibtex_type

        if getattr(item, 'separator', None):
            separators.setdefault(t, []).append(item.separator)
        if item.authors and get_format(item.authors):
            author_formats.setdefault(t, []).append(get_format(item.authors))
        if item.date and len(item.date) > 0 and get_format(item.date[0]):
            date_formats.setdefault(t, []).append(get_format(item.date[0]))
        if getattr(item, 'date_position', None) and not getattr(item, 'online', False):
            date_positions.setdefault(t, []).append(item.date_position)

        item_title_fmt = get_format(item.title) if item.title else None
        if item_title_fmt == 'italic+quotes':
            item_title_fmt = 'quotes'
        if item_title_fmt and item_title_fmt not in ('sentence_case', 'title_case'):
            title_formats.setdefault(t, []).append(item_title_fmt)

        if item.item.marker_type:
            marker_types.append(item.item.marker_type)

    dominant_separator    = {t: Counter(v).most_common(1)[0][0] for t, v in separators.items()}
    dominant_author_fmt   = {t: Counter(v).most_common(1)[0][0] for t, v in author_formats.items()}
    dominant_date_fmt     = {t: Counter(v).most_common(1)[0][0] for t, v in date_formats.items()}
    dominant_title_fmt    = {t: Counter(v).most_common(1)[0][0] for t, v in title_formats.items()}
    dominant_date_pos     = {t: Counter(v).most_common(1)[0][0] for t, v in date_positions.items()}
    dominant_marker       = Counter(marker_types).most_common(1)[0][0] if marker_types else None

    for item in Bib_context.items:
        block = bib_blocks.get(item.item.item_id)
        if block is None:
            continue

        t = item.bibtex_type

        if getattr(item, 'separator', None) and t in dominant_separator:
            if item.separator != dominant_separator[t]:
                matches = check_item_words(matches, item, block, "SEPARATOR_COHERENCE", Category_and_message["SEPARATOR_COHERENCE"], item.content)

        author_fmt = get_format(item.authors)
        if author_fmt and author_fmt not in ('different', 'Jan Nowak') and t in dominant_author_fmt:
            if author_fmt != dominant_author_fmt[t]:
                matches = check_item_words(matches, item, block, "AUTHOR_FORMAT_COHERENCE", Category_and_message["AUTHOR_FORMAT_COHERENCE"], item.content)

        if item.date and len(item.date) > 0 and t in dominant_date_fmt:
            dom_date_fmt = dominant_date_fmt[t]
            equivalent_formats = [
                {"(yyyy)", "yyyy", "YYYY", "(YYYY)"},               
                {"dd mon yyyy", "dd mies. yyyy"},  
                {"mon yyyy", "mies. yyyy"},  
                {"yyyy-mm-dd", "yyyy.mm.dd", "yyyy/mm/dd"},
                {"DD Month YYYY", "DD miesiąc YYYY"}, 
                {"dd.mm.yyyy", "dd/mm/yyyy", "dd-mm-yyyy"}         
            ]
            
            is_equivalent = False
            for d in item.date:
                item_date_fmt = get_format(d)
                if not item_date_fmt:
                    continue
                    
                if item_date_fmt == dom_date_fmt:
                    is_equivalent = True
                    break
                    
                for group in equivalent_formats:
                    if item_date_fmt.lower() in group and dom_date_fmt.lower() in group:
                        is_equivalent = True
                        break 
                
                if is_equivalent:
                    break
                    
            if not is_equivalent:
                if get_text(item.access_date) and get_text(item.access_date).lower() != "[online]":
                    matches = check_item_words(matches, item, block, "DATE_FORMAT_COHERENCE", Category_and_message["DATE_FORMAT_COHERENCE"], item.content)

        if t in dominant_title_fmt:
            item_title_fmt = get_format(item.title) if item.title else None
            if item_title_fmt == 'italic+quotes':  
                item_title_fmt = 'quotes'
            title_text = get_text(item.title) or ""
            if item_title_fmt and item_title_fmt not in ('sentence_case', 'title_case'):  
                if t not in ('article', 'incollection', 'online', 'inproceedings'):  
                    if t in dominant_title_fmt and item_title_fmt != dominant_title_fmt[t]:
                        if not title_text.startswith('(') and len(title_text) > 10:
                            matches = check_item_words(matches, item, block, "TITLE_FORMAT_COHERENCE", Category_and_message["TITLE_FORMAT_COHERENCE"], item.content)

        if getattr(item, 'date_position', None) and t in dominant_date_pos and not getattr(item, 'online', False):
            if item.date_position != dominant_date_pos[t]:
                matches = check_item_words(matches, item, block, "DATE_POSITION_COHERENCE", Category_and_message["DATE_POSITION_COHERENCE"], item.content)

    return matches
