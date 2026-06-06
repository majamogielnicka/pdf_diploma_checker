"""
Moduł zawierający funkcje pomocnicze do walidacji pojedynczych elementów listy.

"""
from .helpers import nlp_pl, nlp_en
import re

NLP_MODELS: dict = {
    "pl": nlp_pl,
    "en": nlp_en,
}

def get_nlp(language):
    return NLP_MODELS[language]

def has_verb(text, language):
    nlp = get_nlp(language)
    return any(token.pos_ in ("VERB", "AUX") for token in nlp(text))

def is_upper_and_dot(full_text):
    if not full_text:
        return False
    return full_text[0].isupper() and full_text.endswith(".")

def check_item(full_text, last_item, second_to_last, text_language, sentence_style, dominant_ending, marker_type):

    strip_open = '\u201e\u00ab\u201c\u2018"'
    strip_close = '\u201d\u00bb\u201d\u2019"'
    full_text = full_text.lstrip(strip_open + '(')
    full_text = full_text.strip(")(")
    if not full_text:
        return True
    trailing_paren = re.search(r'\([^()]*\)\s*([.;,:!]?)\s*$', full_text)
    if trailing_paren:
        after_paren = trailing_paren.group(1)
        if after_paren:
            full_text = full_text[:trailing_paren.start()].rstrip() + after_paren
        else:
            before_paren = full_text[:trailing_paren.start()].rstrip()
            if before_paren:
                full_text = before_paren
            else:
                full_text = full_text.rstrip(strip_close + ')') or full_text

    if len(full_text) >= 2 and full_text[-1] in '.;,:!' and full_text[-2] in strip_close:
        full_text = full_text[:-2] + full_text[-1]
    elif full_text[-1] in strip_close:
        full_text = full_text.rstrip(strip_close) or full_text

    is_en = True if text_language == "en" else False
    if full_text.endswith(':'):
        return True
    if has_verb(full_text, text_language) and sentence_style:
        if dominant_ending in {',', ';'}:
            if last_item:
                return full_text.endswith(('.', ':'))
            return full_text[-1] == dominant_ending
        return is_upper_and_dot(full_text)
    else:
        if not full_text[0].islower() and not is_en:
            if dominant_ending in {',', ';'}:
                if last_item:
                    return full_text.endswith(('.', ':'))
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
                    return full_text.endswith(('.', ':'))
                return full_text[-1] == dominant_ending
            else:
                return full_text[-1].isalnum()
        if last_item:
            return full_text.endswith((".", ':')) or (is_en and full_text[-1].isalnum())
        if second_to_last and is_en:
            return full_text.endswith(("; and", "; or", ",", ";", ", and", ", or", ":")) or full_text[-1].isalnum()
        return full_text.endswith((";", ",", ":")) or (is_en and full_text[-1].isalnum())