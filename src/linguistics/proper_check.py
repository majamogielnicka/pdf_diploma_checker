import re
from src.linguistics.spacy_helpers import lemmatization
from src.redaction.schema import ParagraphBlock, WordInfo
from src.linguistics.linguistics_types import Error_type


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
    content = match.content
    block_words = block.words
    words = []
    if any(char.isdigit() for char in content):
        return True
    elif regex.search(content) != None:
        return True
    elif content.isupper():
        return True
    elif content.isascii() == True:
        return True
    else:
        for word in block_words:    
            for word_id in match.word_idxs:
                if word.word_index == word_id:
                    words.append(word)
        for word in words:
            for proper in proper_names:
                proper_lemma, is_found = lemmatization(proper, text_language)
                if word.text == proper:
                    return True
                if lemma == proper_lemma:
                    return True
            if word.italic:
                return True
            elif word.bold:
                return True

    return False
    









