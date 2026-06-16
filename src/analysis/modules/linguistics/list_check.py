from .check_item_in_list import check_item, has_verb, is_upper_and_dot
from .helpers import add_match
import re

def add_list_error(items_by_id, num, block_id, category, lang):
    """
    Creates and returns an error match object for a specific list item and category.
    """

    if lang =="pl":
        Category_and_message = {
        "LIST_CASING": "Niepoprawna wielkość litery na początku elementu wyliczenia.",
        "LIST_ENDING": "Niepoprawne zakończenie elementu wyliczenia.",
    }
    else:
        Category_and_message = {
        "LIST_CASING": "Incorrect casing at the beginning of a list item.",
        "LIST_ENDING": "Incorrect ending of a list item.",
    }

    item = items_by_id[num]
    if not item.words:
        return None
    word_idxs = [word.word_index for word in item.words]
    page_start = item.words[0].page_number
    page_end = item.words[-1].page_number
    error_coordinate = [{"page": item.words[-1].page_number, "coordinates": list(item.words[-1].bbox)}]
    return add_match(item.text, block_id, page_start, page_end, word_idxs, error_coordinate, category, Category_and_message[category])

def is_short_definition(text, text_language):
    """
    Determines if the text has the structure of a short definition.
    """

    if re.match(r'^[A-Z]{2,}\s+[–—\-−‐‑‒:]\s', text):
        return True
    if re.match(r'^.{1,30}\s+to\s+', text):
        return True
    match = re.match(r'^((\S+\s){1,4})[–—\-−‐‑‒:]\s', text)
    if match:
        prefix = match.group(1)
        return not has_verb(prefix, text_language)
    return False

def check_coherence_in_list(blocks, proper_names, acronyms):
    """
    Analyses document blocks to find inconsistencies in list casing, endings, and coherence.
    """
    matches = []
    #symbols = set(r"""`~!@#$%^&*()_-+={[}}|\:;"'<,>.?/""")
    quote_marks = {'"', '„', '”', '«', '»', '('}
    dash_chars = r'–—\-−‐‑‒'
    definition_search = re.compile(r'^[A-Z]+\s?\(.*?\)\s[' + dash_chars + r']\s')
    definition_sep_pattern = re.compile(r'^(\S+(?:\s+\S+){0,3})\s+[' + dash_chars + r':]\s')
    current_heading = ""
    for b in blocks:
        block = b.block
        if block.type == "list" and block.is_bibliography: 
            continue
        if block.type == "heading":
            current_heading = block.content.upper()
            continue
            
        if any(h in current_heading for h in ["LISTA SKRÓTÓW", "WYKAZ SKRÓTÓW", "SPIS TREŚCI", "SPIS RYSUNKÓW", "SPIS TABEL", "BIBLIOGRAFIA"]):
            continue
        language = b.language
        msg_language = getattr(block, 'language', None) or language
        if block.type == "list":            
            casing_error_ids = []
            ending_error_ids = []
            items_by_id = {}
            marker_error_ids = set()
            for item in block.items:
                items_by_id[item.item_id] = item
            quote_close = {'"', '»', '”', '’', '"', ')'}
            upper_id, lower_id, neutral_id, quote_id, definition_id, endings = [], [], [], [], [], []
            for item in block.items:
                item_text = re.sub(r'\s+', ' ', re.sub(r'\[\d+\]', '', item.text)).strip()
                if not item_text:
                    continue
                effective_text = item_text
                starts_with_quote = item_text[0] in quote_marks
                if starts_with_quote:
                    effective_text = item_text[1:].lstrip()
                    if not effective_text:
                        quote_id.append(item.item_id)
                        continue
                if (definition_search.match(effective_text) or is_short_definition(effective_text, language)
                        or definition_sep_pattern.match(effective_text)):
                    definition_id.append(item.item_id)
                    continue
                if re.search(r'\((?:ang\.|pol\.|fr\.|niem\.|łac\.)\s+', effective_text):
                    definition_id.append(item.item_id)
                    continue
                if item.words and len(item.words) >= 2:
                    first_font = (item.words[0].font, item.words[0].italic)
                    rest_words = [w for w in item.words[1:] if w.text.strip()]
                    if rest_words:
                        rest_fonts = [(w.font, w.italic) for w in rest_words]
                        dominant_font = max(set(rest_fonts), key=rest_fonts.count)
                        if first_font != dominant_font:
                            definition_id.append(item.item_id)
                            end_char = item_text[-1]
                            if end_char in quote_close and len(item_text) >= 2:
                                end_char = item_text[-2] if item_text[-2] not in quote_close else end_char
                            endings.append(end_char)
                            continue
                if effective_text[0].isupper():
                    is_known = False
                    if starts_with_quote:
                        neutral_id.append(item.item_id)
                        is_known = True
                    if not is_known:
                        for proper in proper_names:
                            proper_text = proper[0] if isinstance(proper, tuple) else proper
                            if not proper_text or not proper_text.strip():
                                continue
                            first_word = proper_text.split()[0]
                            if re.match(re.escape(first_word) + r'\s', effective_text):
                                neutral_id.append(item.item_id)
                                is_known = True
                                break
                    if not is_known:
                        for abbreviation in acronyms:
                            abbr_text = abbreviation[0] if isinstance(abbreviation, tuple) else abbreviation
                            if re.match(re.escape(abbr_text) + r'\s', effective_text):
                                neutral_id.append(item.item_id)
                                is_known = True
                                break
                    if not is_known:
                        upper_id.append(item.item_id)
                elif effective_text[0].islower():
                    lower_id.append(item.item_id)
                else:
                    neutral_id.append(item.item_id)
                end_char = item_text[-1]
                if end_char in quote_close and len(item_text) >= 2:
                    end_char = item_text[-2] if item_text[-2] not in quote_close else end_char
                endings.append(end_char)
            if endings:
                dominant_ending = max(sorted(set(endings)), key=endings.count)

            all_definition_like = True
            for item in block.items:
                if item.item_id not in definition_id and item.item_id not in quote_id:
                    item_text = re.sub(r'\s+', ' ', re.sub(r'\[\d+\]', '', item.text)).strip()
                    has_separator = bool(re.search(r'\s[' + dash_chars + r':]\s', item_text))
                    if not has_separator:
                        all_definition_like = False
                        break
            if all_definition_like:
                continue
            inconsistent_list_ids = set()
            inconsistent_list_ids.update(quote_id + definition_id)
            inconsistent = False
            if len(upper_id) > len(lower_id):
                sentence_style = True
            elif len(upper_id) == len(lower_id):
                upper_items_text = [items_by_id[i].text for i in upper_id]
                upper_has_verb = sum(has_verb(t, language) for t in upper_items_text)
                if upper_has_verb > len(upper_id) / 2:
                    inconsistent = False
                    sentence_style = True
                else:
                    inconsistent = True
                    sentence_style = False
            elif len(neutral_id) == len(block.items):
                inconsistent = False
                sentence_style = False
            else:
                sentence_style = False

            inconsistent_list = []

            if inconsistent:
                casing_error_ids.extend(upper_id + lower_id)
                inconsistent_list_ids.update(upper_id + lower_id)
            else:
                inconsistent_list = lower_id if sentence_style else upper_id
                for item_id in inconsistent_list:
                    casing_error_ids.append(item_id)
                    inconsistent_list_ids.add(item_id)
            for item in block.items:
                if item.item_id in inconsistent_list_ids:
                    continue
                if item.item_id in marker_error_ids:
                    continue
                last_item = False
                second_to_last = False

                full_text = re.sub(r'\s+', ' ', re.sub(r'\[\d+\]', '', item.text)).strip()
                if not full_text:
                    continue
                if len(block.items) == 1:
                    last_item = True
                else:
                    if item == block.items[-1]:
                        last_item = True
                    elif item == block.items[-2]:
                        second_to_last = True
            
                if item.marker_type =="number_with_dot" or item.marker_type == "letter_with_dot":
                    if is_upper_and_dot(full_text):
                        continue
                    elif full_text.endswith(':'):
                        continue
                    elif item.item_id in neutral_id:
                        match = re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', full_text)
                        if match:
                            if not check_item(full_text[match.start():], last_item, second_to_last, language, sentence_style, dominant_ending, item.marker_type):
                                ending_error_ids.append(item.item_id)
                        continue
                    else:
                        ending_error_ids.append(item.item_id)
                else: 
                    if len(full_text.split()) < 3:
                        continue
                    if item.item_id in neutral_id:
                        match = re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', full_text)
                        if match:
                            if not check_item(full_text[match.start():], last_item, second_to_last, language, sentence_style, dominant_ending, item.marker_type):
                                ending_error_ids.append(item.item_id)
                        continue
                    if not check_item(full_text, last_item, second_to_last, language, sentence_style, dominant_ending, item.marker_type):
                        ending_error_ids.append(item.item_id)
                
            for num in casing_error_ids:
                error = add_list_error(items_by_id, num, block.block_id, "LIST_CASING", msg_language)
                if error:
                    matches.append(error)
            for num in ending_error_ids:
                error = add_list_error(items_by_id, num, block.block_id, "LIST_ENDING", msg_language)
                if error:
                    matches.append(error)

    return matches
