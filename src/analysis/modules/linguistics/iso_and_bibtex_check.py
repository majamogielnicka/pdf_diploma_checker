from .helpers import add_match, get_match_info
import re
from collections import Counter 

def check_item_words(matches, item, block, category, message, content):
    """
    Adds a match error with coordinates for a specific bibliography item.
    """
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
    """
    Extracts the text value from a parsed bibliography field.
    """
    if not field or not isinstance(field, dict):
        return None
    return next(iter(field.keys()), None)

def get_format(field):
    """
    Extracts the format attribute from a parsed bibliography field.
    """
    if not field or not isinstance(field, dict):
        return None
    return next(iter(field.values()), None)

def check_order(item):
    """
    Determines the order of fields in a bibliography item based on their positions in the text.
    """
    
    text = item.content
    positions = {}
    
    field_map = {
        'authors':    get_text(item.authors) if item.authors else None,
        'title':      get_text(item.title) if item.title else None,
        'journal':    get_text(getattr(item, 'journal', None)),
        'volume':     get_text(item.volume) if item.volume else None,
        'pages':      get_text(item.pages) if item.pages else None,
        'publisher':  get_text(item.publisher) if item.publisher else None,
        'book_title': get_text(item.book_title) if item.book_title else None,
        'url':        get_text(item.url) if item.url else None,
        'access_date':get_text(item.access_date) if item.access_date else None,
    }
    if item.date and len(item.date) > 0:
        field_map['date'] = get_text(item.date[0])

    min_len = 4

    for name, val in field_map.items():
        if val and len(val) >= min_len:
            pos = text.find(val)
            if pos != -1:
                positions[name] = pos

    return tuple(sorted(positions.keys(), key=lambda k: positions[k]))

def get_field_separator(item):
    """
    Identifies the most common separator character used between fields in a bibliography item.
    """

    text = item.content
    separators = []
    if item.authors and get_text(item.authors):
        auth_str = get_text(item.authors)
        pos = text.find(auth_str)
        if pos != -1:
            end_pos = pos + len(auth_str)
            after = text[end_pos:].strip()
            match_date = re.match(r'^\s*\(\d{4}[^\)]*\)', after)
            if match_date:
                end_pos += match_date.end()
                after = text[end_pos:].strip()
            
            sep = re.match(r'^[.,;:]', after)
            if sep:
                separators.append(sep.group(0))
    if item.title and get_text(item.title):
        title_str = get_text(item.title)
        pos = text.find(title_str)
        if pos != -1:
            end_pos = pos + len(title_str)
            after = text[end_pos:].strip()
            while after and after[0] in '"”’\'':
                end_pos += 1
                after = text[end_pos:].strip()
            sep = re.match(r'^[.,;:]', after)
            if sep:
                separators.append(sep.group(0))

    return Counter(separators).most_common()[0][0] if separators else None

def check_iso(matches, item, block):
    """
    Verifies the presence of a final dot in bibliography items.
    """

    if block.language == "pl":
        Category_and_message = {
            "MISSING_FINAL_DOT": "Nie zastosowano kropki na końcu wpisu.",
        }
    else:
        Category_and_message = {
            "MISSING_FINAL_DOT": "A final dot was not used at the end of the entry.",
        }
    text = item.content.strip()
    ends_with_url = bool(re.search(r'https?:\s*//\S+$|www\.\S+$|doi\.org/\S+$', text))
    if not text.endswith('.') and not ends_with_url:
        matches = check_item_words(matches, item, block, "MISSING_FINAL_DOT", Category_and_message["MISSING_FINAL_DOT"], text)

    if item.authors and get_text(item.authors):
        item.separator = get_field_separator(item)

    return matches

def add_bibtex_type(Bib_context):
    """
    Assigns the BibTeX type for each bibliography item based on its content.
    """
    
    keywords = {
    'proceedings', 'conference', 'symposium', 'workshop', 'congress',
    'konferencja', 'konferencji', 'seminarium', 'international',
    'handbook', 'monograph'
    }

    for item in Bib_context.items:
        has_url = bool(item.url and get_text(item.url))
        has_access_date = bool(item.access_date and get_text(item.access_date))
        has_pub_date = bool(item.date and len(item.date) > 0 and get_text(item.date[0]))
        has_journal = bool(getattr(item, 'journal', None) and get_text(item.journal))
        
        publisher_text = get_text(item.publisher) or ""
        publisher_fmt = get_format(item.publisher) if item.publisher else None
        publisher_is_journal = publisher_fmt == 'italic'
        publisher_is_proceedings = (
            publisher_is_journal and
            any(kw in publisher_text.lower() for kw in keywords)
        )
        
        has_publisher = bool(item.publisher and get_text(item.publisher))

        if publisher_is_proceedings:
            item.bibtex_type = "inproceedings"
            if not getattr(item, 'book_title', None):
                item.book_title = item.publisher
                item.publisher = None
        elif has_journal or publisher_is_journal:
            item.bibtex_type = "article"
            if not getattr(item, 'journal', None):
                item.journal = item.publisher
                item.publisher = None
        elif has_publisher:
            item.bibtex_type = "book"
        elif getattr(item, 'online', False) or has_url:
            item.bibtex_type = "online"
            if not getattr(item, 'journal', None):
                item.journal = item.publisher
                item.publisher = None
        else:
            raw_text = item.content.lower()
            
            if "arxiv" in raw_text or "preprint" in raw_text or "tech. rep" in raw_text or "technical report" in raw_text:
                item.bibtex_type = "article"
            elif any(kw in raw_text for kw in keywords): 
                item.bibtex_type = "inproceedings"
            elif "journal" in raw_text or "transactions" in raw_text or "letters" in raw_text or "ieee access" in raw_text or re.search(r'\d+\(\d+\)', raw_text):
                item.bibtex_type = "article"
            else:
                item.bibtex_type = None

def check_bibtex(matches, Bib_context, bib_blocks):
    """
    Validates bibliography items against BibTeX-specific requirements and required fields.
    """
    
    Category_and_message = {
        "WRONG_BIBTEX_TYPE": "Nieznany typ wpisu w bibliografii.",
        "MISSING_BIBTEX_FIELD": "Brakuje wymaganego pola dla tego typu wpisu BibTeX.",
    }
    Category_and_message_eng = {
        "WRONG_BIBTEX_TYPE": "Unknown BibTeX entry type.",
        "MISSING_BIBTEX_FIELD": "Required field missing for this BibTeX entry type.",
    }
    required_fields_per_type = {
        "article": ["journal"],
    }

    add_bibtex_type(Bib_context)
    for item in Bib_context.items:
        block = bib_blocks.get(item.item.item_id)
        if block is None:
            continue
        messages = Category_and_message_eng if block.language == 'en' else Category_and_message
        if item.bibtex_type is None:
            matches = check_item_words(matches, item, block, "WRONG_BIBTEX_TYPE", messages["WRONG_BIBTEX_TYPE"], item.content)
            continue 
        check_item(matches, item, block)

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
                msg = f"{messages['MISSING_BIBTEX_FIELD']} ({item.bibtex_type}: {', '.join(missing)})"
                matches = check_item_words(matches, item, block, "MISSING_BIBTEX_FIELD", msg, item.content)

    return matches

def check_item(matches, item, block):
    """
    Checks a bibliography item for missing obligatory fields based on its type.
    """
    if block.language == "pl":
        Category_and_message = {
            "MISSING_OBLIGATORY": "We wpisie brakuje pól wymaganych (autor, tytuł lub data)",
            "MISSING_PUBLISHER": "Brakuje wydawcy dla pozycji książkowej.",
            "MISSING_ONLINE": "Brakuje pól obowiązkowych dla prac online.",
            "MISSING_PAGES": "Brakuje stron dla artykułu.",
            "MISSING_ARTICLE_OR_BOOK": "Brakuje danych identyfikacyjnych pracy.",
            "NO_ACCESS_DATE_OR_DOI": "Brakuje daty dostępu lub doi.",
        }
    else:
        Category_and_message = {
            "MISSING_OBLIGATORY": "Entry is missing required fields (author, title, or date).",
            "MISSING_PUBLISHER": "Missing publisher for a book entry.",
            "MISSING_ONLINE": "Missing required fields for an online entry.",
            "MISSING_PAGES": "Missing page numbers for an article.",
            "MISSING_ARTICLE_OR_BOOK": "Missing identifying information for the work.",
            "NO_ACCESS_DATE_OR_DOI": "Missing access date or DOI.",
        }
    text = item.content.strip()
    
    if item.bibtex_type != "online":
        if not get_text(item.authors) or (not item.date or len(item.date) == 0 or not get_text(item.date[0])):
            matches = check_item_words(matches, item, block, "MISSING_OBLIGATORY", Category_and_message["MISSING_OBLIGATORY"], text)
            return matches

    if item.bibtex_type =="book" and (not item.publisher or not get_text(item.publisher)):
        matches = check_item_words(matches, item, block, "MISSING_PUBLISHER", Category_and_message["MISSING_PUBLISHER"], text)

    if item.bibtex_type == "online":
        if not item.access_date or not get_text(item.access_date):
            has_valid_pub_date = False
            if item.date and len(item.date) > 0:
                date_text = get_text(item.date[0])
                if date_text and "n.d." not in date_text.lower():
                    has_valid_pub_date = True
            
            is_wiki = "wikipedia" in text.lower() or "wiki" in text.lower()
            
            if not has_valid_pub_date or is_wiki:
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

    if item.url and get_text(item.url) and not get_text(item.doi) and (not item.access_date or not get_text(item.access_date)) and item.bibtex_type != "online":
        matches = check_item_words(matches, item, block, "NO_ACCESS_DATE_OR_DOI", Category_and_message["NO_ACCESS_DATE_OR_DOI"], text)
    
    return matches

def check_coherence_iso(matches, Bib_context, bib_blocks):
    """
    Checks the overall coherence of formatting (separators, dates, authors) across all bibliography items.
    """
    Category_and_message = {
        "SEPARATOR_COHERENCE": "Niespójna forma separatora pól wpisu z pozostałymi wpisami bibliografii.",
        "AUTHOR_FORMAT_COHERENCE": "Niespójny format autorów wpisu z pozostałymi wpisami bibliografii.",
        "DATE_FORMAT_COHERENCE": "Niespójny format dat wpisu z pozostałymi wpisami bibliografii.",
        "TITLE_FORMAT_COHERENCE": "Niespójny format tytułów wpisu z pozostałymi wpisami bibliografii.",
        "DATE_POSITION_COHERENCE": "Niespójna pozycja daty wpisu z pozostałymi wpisami bibliografii.",
        "WRONG_ORDER_ISO": "Kolejność bądź formatowanie pól we wpisie niespójna z resztą bibliografii.",
    }
    Category_and_message_eng = {
        "SEPARATOR_COHERENCE": "Inconsistent field separator format in the entry compared to other bibliography entries.",
        "AUTHOR_FORMAT_COHERENCE": "Inconsistent author format in the entry compared to other bibliography entries.",
        "DATE_FORMAT_COHERENCE": "Inconsistent date format in the entry compared to other bibliography entries.",
        "TITLE_FORMAT_COHERENCE": "Inconsistent title format in the entry compared to other bibliography entries.",
        "DATE_POSITION_COHERENCE": "Inconsistent date position in the entry compared to other bibliography entries.",
        "WRONG_ORDER_ISO": "Order or formatting of fields in the entry is inconsistent with the rest of the bibliography.",
    }

    add_bibtex_type(Bib_context)
    separators, author_formats = {}, {}
    date_formats, title_formats = {}, {}
    date_positions = {}
    marker_types = []
    field_order = {}

    for item in Bib_context.items:
        block = bib_blocks.get(item.item.item_id)
        if block is None:
            continue
        if block.language == 'en':
            messages = Category_and_message_eng
        else:
            messages = Category_and_message
        check_iso(matches, item, block)
        t = item.bibtex_type

        if getattr(item, 'separator', None):
            separators.setdefault(t, []).append(item.separator)
        if item.authors and get_format(item.authors):
            author_formats.setdefault(t, []).append(get_format(item.authors))
        if item.date:
            for d in item.date:
                fmt = get_format(d)
                if fmt:
                    date_formats.setdefault(t, []).append(fmt)
        if getattr(item, 'date_position', None) and not getattr(item, 'online', False):
            date_positions.setdefault(t, []).append(item.date_position)

        item_title_fmt = get_format(item.title) if item.title else None
        if item_title_fmt == 'italic+quotes':
            item_title_fmt = 'quotes'
        if item_title_fmt and item_title_fmt not in ('sentence_case', 'title_case'):
            title_formats.setdefault(t, []).append(item_title_fmt)

        if item.item.marker_type:
            marker_types.append(item.item.marker_type)

        order = check_order(item)
        if order:
            field_order.setdefault(t, []).append(order)

    dominant_separator = {t: Counter(v).most_common(1)[0][0] for t, v in separators.items()}
    dominant_author_fmt = {t: Counter(v).most_common(1)[0][0] for t, v in author_formats.items()}
    dominant_date_fmt = {t: Counter(v).most_common(1)[0][0] for t, v in date_formats.items()}
    dominant_title_fmt = {t: Counter(v).most_common(1)[0][0] for t, v in title_formats.items()}
    dominant_date_pos = {t: Counter(v).most_common(1)[0][0] for t, v in date_positions.items()}
    dominant_marker = Counter(marker_types).most_common(1)[0][0] if marker_types else None
    dominant_order = {t: Counter(v).most_common(1)[0][0] for t, v in field_order.items()}

    for item in Bib_context.items:
        block = bib_blocks.get(item.item.item_id)
        if block is None:
            continue
        if block.language == 'en':
            messages = Category_and_message_eng
        else:
            messages = Category_and_message

        t = item.bibtex_type

        if getattr(item, 'separator', None) and t in dominant_separator:
            if item.separator != dominant_separator[t]:
                matches = check_item_words(matches, item, block, "SEPARATOR_COHERENCE", messages["SEPARATOR_COHERENCE"], item.content)

        author_fmt = get_format(item.authors)
        if t in dominant_author_fmt and dominant_author_fmt[t] == 'Jan Nowak' and author_fmt in {'Nowak J.', 'Nowak, J.'}:
            pass
        elif author_fmt and author_fmt not in ('different', 'Jan Nowak') and t in dominant_author_fmt:
            if author_fmt != dominant_author_fmt[t]:
                matches = check_item_words(matches, item, block, "AUTHOR_FORMAT_COHERENCE", messages["AUTHOR_FORMAT_COHERENCE"], item.content)

        if item.date and len(item.date) > 0 and t in dominant_date_fmt:
            dom_date_fmt = dominant_date_fmt[t]
            equivalent_formats = [
                {"(yyyy)", "yyyy"},               
                {"dd mon yyyy", "dd mies. yyyy"},  
                {"mon yyyy", "mies. yyyy"},  
                {"yyyy-mm-dd", "yyyy.mm.dd", "yyyy/mm/dd"},
                {"dd month yyyy", "dd miesiąc yyyy"}, 
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
                matches = check_item_words(matches, item, block, "DATE_FORMAT_COHERENCE", messages["DATE_FORMAT_COHERENCE"], item.content)

        if t in dominant_title_fmt:
            item_title_fmt = get_format(item.title) if item.title else None
            if item_title_fmt == 'italic+quotes':  
                item_title_fmt = 'quotes'
            title_text = get_text(item.title) or ""
            if item_title_fmt and item_title_fmt not in ('sentence_case', 'title_case'):  
                if t not in ('article', 'incollection', 'online', 'inproceedings'):  
                    if t in dominant_title_fmt and item_title_fmt != dominant_title_fmt[t]:
                        if not title_text.startswith('(') and len(title_text) > 10:
                            matches = check_item_words(matches, item, block, "TITLE_FORMAT_COHERENCE", messages["TITLE_FORMAT_COHERENCE"], item.content)

        if t in dominant_order:
            item_order = check_order(item)
            dom = dominant_order[t]
            common_fields = [f for f in dom if f in item_order]
            item_filtered = [f for f in item_order if f in common_fields]
            if item_filtered != common_fields:
                matches = check_item_words(matches, item, block, "WRONG_ORDER_ISO", messages["WRONG_ORDER_ISO"], item.content)

        if getattr(item, 'date_position', None) and t in dominant_date_pos and not getattr(item, 'online', False):
            if item.date_position != dominant_date_pos[t]:
                matches = check_item_words(matches, item, block, "DATE_POSITION_COHERENCE", messages["DATE_POSITION_COHERENCE"], item.content)
    return matches
