from linguistics_types import Error_type
import spacy_helpers

NLP_MODELS: dict = {
    "pl": spacy_helpers.nlp_pl,
    "en": spacy_helpers.nlp_en,
}

def add_match(items_by_id, num):

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
                content = item['text'],
                category = "LIST_COHERENCE",
                message = "Wyliczenia nie są spójne lub nie zgadzają się z zasadami interpunkcji.",
                offset = 0,
                error_length = len(item['text'])
            )

def get_nlp(language):
    return NLP_MODELS[language]

def has_verb(text, language):
    nlp = get_nlp(language)
    return any(token.pos_ in ("VERB", "AUX") for token in nlp(text))

def is_upper_and_dot(full_text):
    return full_text[0].isupper() and full_text.endswith(".")

def check_item(full_text, last_item, second_to_last, text_language, sentence_style):

    """
    Checks and validates the punctuation correctness of a list item.
    
    Args:
        full_text (str): List item text.
        last_item (bool): True if the item is the last in the list.
        second_to_last (bool): True if the item is the second to last in the list.
        text_language (str): Language code: 'pl' for Polish or 'en' for English.
        sentence_style (bool): True if the list uses uppercase.
 
    Returns:
        bool: True if the item is valid, False if it contains an error.
    """

    is_en = True if text_language == "en" else False
    if has_verb(full_text, text_language) and sentence_style:
        return is_upper_and_dot(full_text)
    else:
        if not full_text[0].islower() and not is_en:
            return False
        if last_item:
            return full_text.endswith(".") or (is_en and full_text[-1].isalnum())
        if second_to_last and is_en:
            return full_text.endswith(("; and", "; or", ",", ";", ", and", ", or")) or full_text[-1].isalnum()
        return full_text.endswith((";", ",")) or (is_en and full_text[-1].isalnum())

def check_coherence_in_list(document, text_language):
    """
    Checks for lack of coherence in a list of items.
    
    Args:
        document (dict): Parsed JSON document.
        text_language (str): pl for Polish or en for English.
    
    Returns:
        list[Error_type]: List of detected errors.
    """
    matches = []

    for block in document['logical_blocks']:
        if block['type'] == "list":
            matches_numbers = []
            items_by_id = {item['item_id']: item for item in block['items']}
            upper_id = [item['item_id'] for item in block['items'] if item['text'].strip()[0].isupper()]
            lower_id = [item['item_id'] for item in block['items'] if item['text'].strip()[0].islower()]
            inconsistent = False
            if len(upper_id) > len(lower_id):
                sentence_style = True
            elif len(upper_id) == len(lower_id):
                inconsistent = True
                sentence_style = False
            else:
                sentence_style = False

            inconsistent_list = []
            inconsistent_list_ids = set()
            if inconsistent:
                matches_numbers.extend(upper_id + lower_id)
                inconsistent_list_ids.update(upper_id + lower_id)
            else:
                inconsistent_list = lower_id if sentence_style else upper_id
                for item in inconsistent_list:
                    matches_numbers.append(item)
                    inconsistent_list_ids.add(item)
            for item in block['items']:
                if item['item_id'] in inconsistent_list_ids:
                    continue
                last_item = False
                second_to_last = False

                full_text = item['text'].strip()

                if len(block['items']) == 1:
                    last_item = True
                else:
                    if item == block['items'][-1]:
                        last_item = True
                    elif item == block['items'][-2]:
                        second_to_last = True
            
                if item['marker_type'] =="number_with_dot" or item['marker_type'] == "letter_with_dot":
                    if is_upper_and_dot(full_text):
                        continue
                    else:
                        matches_numbers.append(item['item_id'])
                else:               
                    if not check_item(full_text, last_item, second_to_last, text_language, sentence_style):
                        matches_numbers.append(item['item_id'])
                
            if len(matches_numbers) != 0:
                for num in matches_numbers:
                    match = add_match(items_by_id, num)
                    matches.append(match)

    return matches