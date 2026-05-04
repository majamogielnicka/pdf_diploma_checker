from helpers import nlp_en
import re
'''
Skrypt sprawdzający kompletność bibliografii i sprawdzający jej zgodność z wybranym stylem bibliograficznym: 
(pn-iso 690:2012, APA, IEEE, Harvard)
'''

def check_bibliography(blocks):
    matches = []
    '''TODO: wykrycie wszystkich typów cytowań i rozróżnienie co jest czym, 
        sprawdzenie spójności - iso
        sprawdzenie konkretnych stylów
        sprawdzenie wymagać bibtex
    '''

    date_patterns = {
        r'\d{1,2}/\d{1,2}/[12]\d{3}\b':          'dd/mm/yyyy',
        r'[12]\d{3}/\d{1,2}/\d{1,2}\b':          'yyyy/mm/dd',
        r'\d{1,2}-\d{1,2}-[12]\d{3}\b':          'dd-mm-yyyy',
        r'\b[12]\d{3}-\d{1,2}-\d{1,2}\b':        'yyyy-mm-dd',
        r'\d{1,2}\.\d{1,2}\.[12]\d{3}\b':        'dd.mm.yyyy',
        r'\b[12]\d{3}\.\d{1,2}\.\d{1,2}':        'yyyy.mm.dd',
        r'(?<![\w\/\.\-])[12]\d{3}(?![\w\/\-])':   'yyyy',
    }

    doi_patterns = {
        r'doi\.org/10\.\d{4,9}': 'link',
        r'(DOI|doi)(\s*):\s*10\.\d{4,9}': 'citation',
    }
    #TODO: suffixes
    UPPER_CASE = r'[A-ZĄĆĘŁŃÓŚŹŻÀ-ÖØ-öø-ÿĀ-ž]'
    LOWER_CASE = r'[a-ząćęłńóśźżà-öø-ÿā-ž]'
    special_chars  = rf"([–-'])"
    surname_pattern = rf'{UPPER_CASE}{LOWER_CASE}+({special_chars}({UPPER_CASE}|{LOWER_CASE})+)*'
    fullname_pattern = rf'{UPPER_CASE}{LOWER_CASE}+'
    short_name_pattern = rf'{UPPER_CASE}\.'

    author_patterns = {
        rf'{short_name_pattern}(\s*{short_name_pattern})*\s{surname_pattern}': 'J. Nowak',
        rf'{fullname_pattern}(\s{fullname_pattern})*\s{surname_pattern}': 'Jan Nowak',
        rf'{surname_pattern},\s{short_name_pattern}(\s*{short_name_pattern})*': 'Nowak, J.',
        rf'{surname_pattern},\s{fullname_pattern}(\s{fullname_pattern})*': 'Nowak, Jan',
    }

    #check_title
    return matches