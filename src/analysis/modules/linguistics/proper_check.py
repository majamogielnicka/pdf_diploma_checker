import re
from .spacy_helpers import lemmatization
from src.analysis.extraction.schema import ParagraphBlock, WordInfo
from .linguistics_types import Error_type


def check_if_proper(block, match, proper_names=None, lemma=None, is_diff=None):
    """
    Evaluates whether a particular matched word should be considered a valid exception 
    
    Args:
        block (ParagraphBlock): The block dictionary containing the word objects.
        match (Error_type): The error match object containing the reported typo.
        proper_names (set): A collection of known proper names in the document.
        lemma (str): The lemmatized version of the matched word.
        is_diff (bool): Whether the word is in a different font than the main font.
    Returns:
        bool: True if the word is deemed a proper name/exception, False otherwise.
    """
    ACADEMIC_TITLES = {"prof.", "dr", "dr hab.", "mgr", "inż.", "lic.", "doc."}
    BRITISH_ABBREVIATIONS = {"Dr", "Mr", "Mrs", "Ms", "Jr", "Sr", "St"}
    #regex = re.compile(r'[@_!#$%^&*()<>?/\|}{~:]')
    is_digit = re.compile(r'\d')
    if lemma:
        text = lemma.strip("():;,.!?[]\n\t ")
    else:
        text = match.content.strip("():;,.!?[]\n\t ")
    if is_digit.search(text):
        return True
    #elif regex.search(text) != None:
    #    return True
    if text in ACADEMIC_TITLES or text in BRITISH_ABBREVIATIONS:
        return True
    if text.isupper():
        return True

    target_words_ids = set(match.word_idxs) if isinstance(match.word_idxs, list) else {match.word_idxs}
    matched_words = [word for word in block.words if word.word_index in target_words_ids]

    if proper_names is not None:
        proper = [p[0] for p in proper_names]
        proper_lemmas = [p[1] for p in proper_names]
        for word in matched_words:
            if word.text in proper:
                return True
            if lemma and text in proper_lemmas:
                return True

    if is_diff and matched_words:
        if all((word.italic or word.bold) for word in matched_words):
            return True

    return False
