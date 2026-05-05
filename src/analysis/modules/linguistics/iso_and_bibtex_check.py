from helpers import nlp_en, add_match, get_match_info
import re
from collections import Counter 

def check_order(block, matches, item):
    
    '''
    TODO: sprawdzanie kolejnośći 
    '''

    Category_and_message = {
        "WRONG_ORDER": "Wpis w bibliografii jest w złej kolejności.",
    }
    text = item.content

    return matches
    

def check_iso(block, matches, item):

    Category_and_message = {
        "MISSING_FINAL_DOT": "Nie zastosowano kropki na końcu wpisu.",
        "SEPARATOR_COHERENCE": "Separatory nie są spójne wewnątrz wpisu."
    }
    separator = re.compile(r'[;,]')
    text = item.content.strip()
    if not text.endswith('.'):
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, len(item.content) - 1, 1)
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_FINAL_DOT", Category_and_message["MISSING_FINAL_DOT"]))

    separators = separator.findall(text)
    authors_separator = separator.findall(item.authors)
    dominant_author_separator = Counter(authors_separator).most_common()[0]
    dominant_separator = Counter(separators).most_common()[0]
    if dominant_separator != dominant_author_separator:
        item.separator = dominant_separator
    
    matches.extend(check_order(block, matches, item))

    return matches

def add_bibtex_type(Bib_context):
    
    for item in Bib_context.items:
        if item.journal:
            item.bibtex_type = "article"
        elif item.publisher and not item.journal:
            item.bibtex_type = "book"
        elif item.publisher and item.pages and item.is_tittle_italics:
            item.bibtex_type = "inbook"
        elif item.publisher and item.book_title:
            item.bibtex_type = "incollection"
        elif item.book_title:
            item.bibtex_type = "inproceedings"
        elif item.online or item.url:
            item.bibtex_type = "online"
        elif re.search("rozprawa|thesis|Uniwersytet|Politechnika|University", item.content):
            item.bibtex_type = "thesis"
        else:
            item.bibtex_type = "misc"


def check_bibtex(blocks, matches, Bib_context):
    
    ''' 
    TODO: sprawdzić czy każdy typ ma wszystkie wymagane pola,
    czy wszystkie wpisy są sklasyfikowane
    '''
    add_bibtex_type(Bib_context)

    return matches

def check_item(block, matches, item):

    Category_and_message = {
        "MISSING_FINAL_DOT": "Nie zastosowano kropki na końcu wpisu.",
        "MISSING_OBLIGATORY": "Brakuje autorów, tytułu lub daty.",
        "SEPARATOR_COHERENCE": "Separatory nie są spójne wewnątrz wpisu.",
        "MISSING_ONLINE": "Brakuje pól obowiązkowych dla prac online.",
        "MISSING_JOURNAL": "Brakuje stron dla artykułu."
    }
    text = item.content.strip()
    if item.authors == None or item.publisher == None or item.title == None or item.date == None:
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, 0, len(item.content))
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_OBLIGATORY", Category_and_message["MISSING_OBLIGATORY"]))
    if item.online: 
        if not item.access_date:
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, 0, len(item.content))
            matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_ONLINE", Category_and_message["MISSING_ONLINE"]))
        if not item.url and not item.doi:
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, 0, len(item.content))
            matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_ONLINE", Category_and_message["MISSING_ONLINE"]))   
    if item.journal and not item.pages:
        p_start, p_end, word_idx, error_coordinate = get_match_info(block, 0, len(item.content))
        matches.append(add_match(text, block.block_id, p_start, p_end, word_idx, error_coordinate, "MISSING_JOURNAL", Category_and_message["MISSING_JOURNAL"]))

    return matches

def check_coherence_iso(blocks, matches, Bib_context):

    Category_and_message = {
        "SEPARATOR_COHERENCE": "Niespójna forma separatora we wpisach w bibliografii'.",
    }
    blocks_by_id = {b.block_id: b for b in blocks}
    separators, author_formats = [], []
    for item in Bib_context.items:
        separators.append(item.separator)
        author_formats.append(item.author_format)
        block = blocks_by_id.get(item.item.item_id)
        matches.extend(check_item(block, matches, item))
        matches.extend(check_iso(block, matches, item))

    Bib_context.dominant_separator = Counter(separators).most_common()[0]
    Bib_context.dominant_author_format = Counter(author_formats).most_common()[0]

    for item in Bib_context.items:
        if item.separator!=Bib_context.dominant_separator:
            block = blocks_by_id.get(item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, 0, len(item.content))
            matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "SEPARATOR_COHERENCE", Category_and_message["SEPARATOR_COHERENCE"]))
        if item.author_format!=Bib_context.dominant_author_format:
            block = blocks_by_id.get(item.item.item_id)
            p_start, p_end, word_idx, error_coordinate = get_match_info(block, 0, len(item.content))
            matches.append(add_match(item.content, block.block_id, p_start, p_end, word_idx, error_coordinate, "SEPARATOR_COHERENCE", Category_and_message["SEPARATOR_COHERENCE"]))
    
    return matches
