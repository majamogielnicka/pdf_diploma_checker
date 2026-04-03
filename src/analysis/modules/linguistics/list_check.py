from src.linguistics.linguistics_types import Error_type
from src.redaction.schema import ListBlock
from src.linguistics.check_item_in_list import check_item, has_verb, is_upper_and_dot
import re

def add_match(items_by_id, num, block_id):

    """
    Creates an error object for a specific list item.
    
    Args:
        items_by_id (dict): Dictionary of items by ID.
        num (int): Item ID.
    
    Returns:
        Error_type: Error type object.
    """

    item = items_by_id[num]
    return Error_type(
                content = item.text,
                category = "LIST_COHERENCE",
                message = "Wyliczenia nie są spójne lub nie zgadzają się z zasadami interpunkcji.",
                offset = 0,
                error_length = len(item.text),
                block_id = block_id,
                page_start = item.words[0].page_number if item.words else None,
                page_end = item.words[-1].page_number if item.words else None,
                word_idxs = [word.word_index for word in item.words]
            )

def is_short_definition(text, text_language):

    """
    Checks if the text is a short definition.
    
    Args:
        text (str): Text to check.
        text_language (str): pl for Polish or en for English.
    
    Returns:
        bool: True if the text is a short definition, False otherwise.
    """

    match = re.match(r'^((\S+\s){1,4})[–—\-−:]\s', text)
    if match:
        prefix = match.group(1)
        return not has_verb(prefix, text_language)
    return False

def check_coherence_in_list(document, text_language):
    """
    Checks for lack of coherence in a list of items.
    
    Args:
        document (FinalDocument): Parsed JSON document.
        text_language (str): pl for Polish or en for English.
    
    Returns:
        list[Error_type]: List of detected errors.
    """
    matches = []
    symbols = set(r"""`~!@#$%^&*()_-+={[}}|\:;"'<,>.?/""")
    quote_marks = {'"', '„', '”', '«', '»'}

    for block in document.logical_blocks:
        if isinstance(block, ListBlock):            
            matches_numbers = []
            items_by_id = {}
            for item in block.items:
                items_by_id[item.item_id] = item
            upper_id, lower_id, neutral_id, quote_id, definition_id, endings = [], [], [], [], [], []
            for item in block.items:
                item_text = re.sub(r'\s+', ' ', re.sub(r'\[\d+\]', '', item.text)).strip()
                if item_text[0] in quote_marks:
                    quote_id.append(item.item_id)
                    continue
                if (re.match(r'^[A-Z]+\s?\(.*?\)\s[–—\-−]\s', item_text) or is_short_definition(item_text, text_language)):
                    definition_id.append(item.item_id)
                    continue
                if item_text[0].isupper():
                    upper_id.append(item.item_id)
                elif item_text[0].islower():
                    lower_id.append(item.item_id)
                else:
                    neutral_id.append(item.item_id)
                endings.append(item_text[-1])
            if endings:
                dominant_ending = max(sorted(set(endings)), key=endings.count)

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
                upper_has_verb = sum(has_verb(t, text_language) for t in upper_items_text)
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
                matches_numbers.extend(upper_id + lower_id)
                inconsistent_list_ids.update(upper_id + lower_id)
            else:
                inconsistent_list = lower_id if sentence_style else upper_id
                for item in inconsistent_list:
                    matches_numbers.append(item)
                    inconsistent_list_ids.add(item)
            for item in block.items:
                if item.item_id in inconsistent_list_ids:
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
                            if not check_item(full_text[match.start():], last_item, second_to_last, text_language, sentence_style, dominant_ending):
                                matches_numbers.append(item.item_id)
                        continue
                    else:
                        matches_numbers.append(item.item_id)
                else: 
                    if item.item_id in neutral_id:
                        match = re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', full_text)
                        if match:
                            if not check_item(full_text[match.start():], last_item, second_to_last, text_language, sentence_style, dominant_ending):
                                matches_numbers.append(item.item_id)
                        continue
                    if not check_item(full_text, last_item, second_to_last, text_language, sentence_style, dominant_ending):
                        matches_numbers.append(item.item_id)
                
            if len(matches_numbers) != 0:
                for num in matches_numbers:
                    match = add_match(items_by_id, num, block.block_id)
                    matches.append(match)

    return matches
