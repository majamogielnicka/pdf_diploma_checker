from .check_item_in_list import check_item, has_verb, is_upper_and_dot
from .helpers import add_match
import re

def add_list_error(items_by_id, num, block_id, category):

    Category_and_message = {
        "LIST_MARKER": "Zastosowano niepoprawny marker wyliczenia.",
        "LIST_CASING": "Niepoprawna wielkość litery na początku elementu wyliczenia.",
        "LIST_ENDING": "Niepoprawne zakończenie elementu wyliczenia.",
    }
    item = items_by_id[num]
    if not item.words:
        return None
    word_idxs = [word.word_index for word in item.words]
    page_start = item.words[0].page_number
    page_end = item.words[-1].page_number
    error_coordinate = (item.words[-1].bbox[2], item.words[-1].bbox[3])
    return add_match(item.text, block_id, page_start, page_end, word_idxs, error_coordinate, category, Category_and_message[category])

def is_short_definition(text, text_language):

    """
    Checks if the text is a short definition.
    
    Args:
        text (str): Text to check.
        text_language (str): pl for Polish or en for English.
    Returns:
        bool: True if the text is a short definition, False otherwise.
    """
    if re.match(r'^[A-Z]{2,}\s+[–—\-−:]\s', text):
        return True
    match = re.match(r'^((\S+\s){1,4})[–—\-−:]\s', text)
    if match:
        prefix = match.group(1)
        return not has_verb(prefix, text_language)
    return False

def check_coherence_in_list(blocks, proper_names, acronyms):
    """
    Checks for lack of coherence in a list of items.
    
    Args:
        document (FinalDocument): Parsed JSON document.
        text_language (str): pl for Polish or en for English.
    
    Returns:
        list[Error_type]: List of detected errors.
    """
    matches = []
    #symbols = set(r"""`~!@#$%^&*()_-+={[}}|\:;"'<,>.?/""")
    quote_marks = {'"', '„', '”', '«', '»', '('}
    definition_search = re.compile(r'^[A-Z]+\s?\(.*?\)\s[–—\-−]\s')

    for b in blocks:
        block = b.block
        language = b.language
        if block.type == "list":            
            casing_error_ids = []
            ending_error_ids = []
            items_by_id = {}
            marker_error_ids = set()

            for item in block.items:
                items_by_id[item.item_id] = item
                if (item.marker_type == "number_with_bracket" or item.marker_type == "letter_with_dot") and language == "pl":
                    error = add_list_error(items_by_id, item.item_id, block.block_id, "LIST_MARKER")
                    if error:
                        matches.append(error)
                    marker_error_ids.add(item.item_id)
            quote_close = {'"', '»', '”', '’', '"', ')'}
            upper_id, lower_id, neutral_id, quote_id, definition_id, endings = [], [], [], [], [], []
            for item in block.items:
                item_text = re.sub(r'\s+', ' ', re.sub(r'\[\d+\]', '', item.text)).strip()
                effective_text = item_text
                starts_with_quote = item_text[0] in quote_marks
                if starts_with_quote:
                    effective_text = item_text[1:].lstrip()
                    if not effective_text:
                        quote_id.append(item.item_id)
                        continue
                if (definition_search.match(effective_text) or is_short_definition(effective_text, language)):
                    definition_id.append(item.item_id)
                    continue
                if effective_text[0].isupper():
                    is_known = False
                    if starts_with_quote:
                        neutral_id.append(item.item_id)
                        is_known = True
                    if not is_known:
                        for proper in proper_names:
                            proper_text = proper[0] if isinstance(proper, tuple) else proper
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
                if any(',' in item.text[:-2] for item in block.items) and dominant_ending == ',':
                    dominant_ending = ';'

            all_definition_like = True
            for item in block.items:
                if item.item_id not in definition_id and item.item_id not in quote_id:
                    item_text = re.sub(r'\s+', ' ', re.sub(r'\[\d+\]', '', item.text)).strip()
                    has_separator = bool(re.search(r'\s[–—\-−:]\s', item_text))
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
                    elif item.item_id in neutral_id:
                        match = re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', full_text)
                        if match:
                            if not check_item(full_text[match.start():], last_item, second_to_last, language, sentence_style, dominant_ending, item.marker_type):
                                ending_error_ids.append(item.item_id)
                        continue
                    else:
                        ending_error_ids.append(item.item_id)
                else: 
                    if item.item_id in neutral_id:
                        match = re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', full_text)
                        if match:
                            if not check_item(full_text[match.start():], last_item, second_to_last, language, sentence_style, dominant_ending, item.marker_type):
                                ending_error_ids.append(item.item_id)
                        continue
                    if not check_item(full_text, last_item, second_to_last, language, sentence_style, dominant_ending, item.marker_type):
                        ending_error_ids.append(item.item_id)
                
            for num in casing_error_ids:
                error = add_list_error(items_by_id, num, block.block_id, "LIST_CASING")
                if error:
                    matches.append(error)
            for num in ending_error_ids:
                error = add_list_error(items_by_id, num, block.block_id, "LIST_ENDING")
                if error:
                    matches.append(error)

    return matches
