'''
Odrzucanie false positives uzyskanych podczas analizy językowej.
'''

import language_tool_python
from collections import defaultdict
import re
from .helpers import lemmatization
from .proper_check import check_if_proper
import string
 
def check_exeptions(matches, blocks, proper_names):
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
                inside_quotes = check_quotes(match.offset, match.offset + match.error_length, text)
                if not inside_quotes:
                    if match.category == 'TYPOS':
                        try:
                            if any(letter == '-' for letter in match.content):
                                continue
                            elif match.offset > 0 and text[match.offset - 1] == '-':
                                continue
                            elif match.offset + len(match.content) < len(text) and text[match.offset + len(match.content)] == '-':
                                continue
                        except:
                            print(f'błędne koordynaty: {match.content} {match.offset}')
                        lemma, is_found = lemmatization(word, block.language)
                        if check_if_proper(block.block, match, proper_names, lemma):
                            continue
                        potential_exeptions[lemma].append(match)
                        potential_exeption = True
                    if match.category == "CASING" and match.offset == 0:
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


def check_quotes(start, end, text, return_spans=False):
    spans = []
    for quote_match in re.finditer(r'[“„″””\'”"](.+?)[“”″\'"”]', text):
        if return_spans:
            spans.append((quote_match.start(), quote_match.end()))
        elif quote_match.start() < start < quote_match.end() or quote_match.start() < end < quote_match.end():
            return True
    if return_spans:
        return spans
    return False



