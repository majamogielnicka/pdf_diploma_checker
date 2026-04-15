import re
from .spacy_helpers import lemmatization
from src.analysis.extraction.schema import ParagraphBlock, WordInfo
from .linguistics_types import Error_type


def check_if_proper(block, match, proper_names, lemma, text_language):
    """
    Evaluates whether a particular matched word should be considered a valid exception 
    
    Args:
        block (ParagraphBlock): The block dictionary containing the word objects.
        match (Error_type): The error match object containing the reported typo.
        proper_names (set): A collection of known proper names in the document.
        lemma (str): The lemmatized version of the matched word.
        text_language (str): pl for Polish or en for English.
        
    Returns:
        bool: True if the word is deemed a proper name/exception, False otherwise.
    """
    
    regex = re.compile(r'[@_!#$%^&*()<>?/\|}{~:]')
    is_digit = re.compile(r'\d')
    if is_digit.search(lemma):
        return True
    elif regex.search(lemma) != None:
        return True
    elif lemma.isupper():
        return True
    elif lemma.isascii() == True:  
        return True
    else:
        target_words_ids = set(match.word_idxs)
        matched_words = [word for word in block.words if word.word_index in target_words_ids]
        proper = [p[0] for p in proper_names]
        proper_lemmas = [p[1] for p in proper_names]
    for word in matched_words:
            if word.text in proper:
                return True
            if lemma in proper_lemmas:
                return True
            if word.italic or word.bold:
                return True

    return False
