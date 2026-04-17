import language_tool_python
from collections import defaultdict
import re
from .linguistics_types import Error_type
from .spacy_helpers import lemmatization
from src.analysis.extraction.schema import ParagraphBlock
from .proper_check import check_if_proper
import string
 
def check_exeptions(matches, blocks, proper_names):
    '''
    Checks potentially false positive python language tool error with different criteria.
    
    Args:
        matches (list): A list of Error_type, containing python_language_tool errors of type TYPOS
        blocks (list(Block_context)): List contaning Block_context objects.
        proper_names (set): A collection of known proper names in the document.
    Returns:
        valid_errors (list): List of Error_type, containing errors that did not meet the criteria
    '''
    potential_exeptions = defaultdict(list)
    valid_errors = []
    blocks_to_check = defaultdict(list)

    for match in matches:
        blocks_to_check[f'{match.block_id}_{match.page_start}'].append(match)

    for block in blocks:
        block_key = f'{block.block.block_id}_{block.block.words[0].page_number}'
        if block_key in blocks_to_check:
            for match in blocks_to_check[block_key]:
                text = block.contents
                word = match.content
                if word.translate(str.maketrans('', '', string.punctuation)) in proper_names:
                    continue
                potential_exeption = False
                inside_quotes = check_quotes(match, text)
                if not inside_quotes:
                    if match.category == 'TYPOS':
                        lemma, is_found = lemmatization(word, block.language)
                        if check_if_proper(block.block, match, proper_names, lemma):
                            continue
                        potential_exeptions[lemma].append(match)
                        potential_exeption = True
                    if match.category == "CASING" and match.offset == 0:
                    # if match.category == "CASING" and block.type == "heading" and match.offset == 0:
                        continue
                if not inside_quotes and not potential_exeption:
                    valid_errors.append(match)
    exeptions = []    
    for lemma, match_list in potential_exeptions.items():
        if len(match_list) > 2:
            exeptions.extend(match_list)
        else:
            valid_errors.extend(match_list)

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



