import language_tool_python
from collections import defaultdict
import re
from linguistics_types import Error_type
from spacy_helpers import lemmatization

#set for proper_names as we don't need to count them, defaultdict for exeptions as we need to count their occurences and its more optimal than normal dict
exeptions = defaultdict(int)
proper_names = {}

#TODO:thinking of a way to export a set of exeptions, to count they appearances in whole pdf.
#TODO: adjust word coordinates to json yet to be received from redaction group.
def check_exeptions(matches, text, text_language):
    '''
    Checks potentially false positive python language tool error with different criteria.
    
    Args:
        matches (list): A list of Error_type, containing python_language_tool errors of type TYPOS
        text_language (str): pl for Polish or en for English.
        text (str): Text from the currently checked block.
    
    Returns:
        valid_errors (list): List of Error_type, containing errors that did not meet the criteria
    '''

    valid_errors = []
    for match in matches:
        word = match.content
        inside_quotes = check_quotes(match, text)
        if match.category == 'TYPOS':
            proper_name = False
            if match.content.isupper():
                proper_name = True
            #TODO: check with proper name list
            else:
                lemma, is_found = lemmatization(word, text_language)
                exeptions[lemma.lower()] +=1
        if not inside_quotes and not proper_name:
            valid_errors.append(match)
        #check_font()
    print(exeptions)
    return valid_errors


def check_lemma(lemma, text_language):
    '''
    Extracts the lemma of a word
    
    Args:
        word (str): Word to be checked
        text_language (str): pl for Polish or en for English.
    
    Returns:
        tuple(lemma(str), is_found(bool)): A tuple of extracted word and bolean value True if lemma has been found. 
    '''
    is_valid = False
    if text_language == "pl":
        tool_en = language_tool_python.LanguageTool('pl-PL')
        match = tool_en.check(lemma)
    else:
        tool_en = language_tool_python.LanguageTool('en-GB')
        match = tool_en.check(lemma)
    if len(match) == 0:
        is_valid = True
    
    return is_valid

#def check_font


def check_quotes(match, text):   
    '''
    Extracts if typo is inside quotes.
    
    Args:
        match (str): Object type Error_type
        text (str): String of currently checked block
    
    Returns:
        Boolean: True - if match is inside quotes, False if it is not.
    '''
    inside_quotes_matches = re.finditer(r'[„″"](.+?)["”″]',text)
    for quote_match in inside_quotes_matches:
        if match.offset > quote_match.start() and match.offset < quote_match.end():
            return True
    return False



