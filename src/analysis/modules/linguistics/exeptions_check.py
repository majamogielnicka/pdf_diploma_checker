import language_tool_python
from collections import defaultdict
import re
from src.linguistics.linguistics_types import Error_type
from src.linguistics.spacy_helpers import lemmatization
from src.redaction.schema import ParagraphBlock
#from proper_check import check_if_proper

def check_exeptions(matches, blocks, text_language):
    '''
    Checks potentially false positive python language tool error with different criteria.
    
    Args:
        matches (list): A list of Error_type, containing python_language_tool errors of type TYPOS
        text_language (str): pl for Polish or en for English.
        blocks (FinalDocument): contains string and metadata of each word
    
    Returns:
        valid_errors (list): List of Error_type, containing errors that did not meet the criteria
    '''
    potential_exeptions = defaultdict(list)
    valid_errors = []
    blocks_to_check = defaultdict(list)

    for match in matches:
        blocks_to_check[f'{match.block_id}_{match.page_start}'].append(match)

    for block in blocks.logical_blocks:
        if not isinstance(block, ParagraphBlock) or not block.words:
            continue
        block_key = f'{block.block_id}_{block.words[0].page_number}'
        if block_key in blocks_to_check:
            for match in blocks_to_check[block_key]:
                text = block.content
                word = match.content
                potential_exeption = False
                proper_name = False
                inside_quotes = check_quotes(match, text)
                if not inside_quotes and not proper_name:
                    if match.category == 'TYPOS' or match.category == 'CASING':
                        if match.category == 'TYPOS':
                            lemma, is_found = lemmatization(word, text_language)
                            # if check_if_proper(block, match, proper_names, lemma, text_language):
                            #     continue
                            potential_exeptions[lemma].append(match)
                            potential_exeption = True
                if not inside_quotes and not proper_name and not potential_exeption:
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



