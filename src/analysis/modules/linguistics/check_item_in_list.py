from . import spacy_helpers

NLP_MODELS: dict = {
    "pl": spacy_helpers.nlp_pl,
    "en": spacy_helpers.nlp_en,
}

def get_nlp(language):
    return NLP_MODELS[language]

def has_verb(text, language):
    nlp = get_nlp(language)
    return any(token.pos_ in ("VERB", "AUX") for token in nlp(text))

def is_upper_and_dot(full_text):
    return full_text[0].isupper() and full_text.endswith(".")

def check_item(full_text, last_item, second_to_last, text_language, sentence_style, dominant_ending, marker_type):

    """
    Checks and validates the punctuation correctness of a list item.
    
    Args:
        full_text (str): List item text.
        last_item (bool): True if the item is the last in the list.
        second_to_last (bool): True if the item is the second to last in the list.
        text_language (str): Language code: 'pl' for Polish or 'en' for English.
        sentence_style (bool): True if the list uses uppercase.
        dominant_ending (str): The dominant ending of the list items.
        marker_type (str): The marker type of the list item.
    Returns:
        bool: True if the item is valid, False if it contains an error.
    """
    STRIP_OPEN = '\u201e\u00ab\u201c\u2018"('
    STRIP_CLOSE = '\u201d\u00bb\u201d\u2019")'
    full_text = full_text.lstrip(STRIP_OPEN)
    if not full_text:
        return True
    if len(full_text) >= 2 and full_text[-1] in '.;,:!' and full_text[-2] in STRIP_CLOSE:
        full_text = full_text[:-2] + full_text[-1]
    elif full_text[-1] in STRIP_CLOSE:
        full_text = full_text.rstrip(STRIP_CLOSE) or full_text

    is_en = True if text_language == "en" else False
    if has_verb(full_text, text_language) and sentence_style:
        return is_upper_and_dot(full_text)
    else:
        if not full_text[0].islower() and not is_en:
            if dominant_ending in {',', ';'}:
                if last_item:
                    return full_text.endswith('.')
                return full_text[-1] == dominant_ending
            return full_text.endswith('.')
        if marker_type in ("dash", "bullet") and not has_verb(full_text, text_language) and ',' not in full_text[:-2]:
            if len(full_text.split()) < 5 and full_text[-1].isalnum():
                return True
        if is_en and dominant_ending:
            if not has_verb(full_text, text_language) and not sentence_style:
                return full_text[-1].isalnum()
            if dominant_ending == '.':
                return full_text.endswith('.')
            elif dominant_ending in {',', ';'}:
                if last_item:
                    return full_text.endswith('.')
                return full_text[-1] == dominant_ending
            else:
                return full_text[-1].isalnum()
        if last_item:
            return full_text.endswith(".") or (is_en and full_text[-1].isalnum())
        if second_to_last and is_en:
            return full_text.endswith(("; and", "; or", ",", ";", ", and", ", or")) or full_text[-1].isalnum()
        return full_text.endswith((";", ",")) or (is_en and full_text[-1].isalnum())