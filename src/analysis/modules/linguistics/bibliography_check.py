from .helpers import nlp_en, add_match, get_match_info
import re
from .iso_and_bibtex_check import check_bibtex, check_coherence_iso
from .linguistics_types import Bibliography_context, Bib_item_context
'''
Skrypt sprawdzający kompletność bibliografii i sprawdzający jej zgodność z wybranym stylem bibliograficznym: 
docelowo: (pn-iso 690:2012, APA 7, IEEE, Harvard 4)
'''

def check_bibliography(blocks, producer):
    matches = []
    '''TODO: wykrycie wszystkich typów cytowań i rozróżnienie co jest czym, 
        sprawdzenie spójności - iso
        sprawdzenie konkretnych stylów
        sprawdzenie wymagać bibtex
    '''

    date_patterns = {
        r'(?<![\w\/\.\-])(?<!\d\.)\d{1,2}/\d{1,2}/[12]\d{3}\b(?![\w\/\-])(?!\.\d)': 'dd/mm/yyyy',
        r'(?<![\w\/\.\-])(?<!\d\.)[12]\d{3}/\d{1,2}/\d{1,2}\b(?![\w\/\-])(?!\.\d)': 'yyyy/mm/dd',
        r'(?<![\w\/\.\-])(?<!\d\.)\d{1,2}-\d{1,2}-[12]\d{3}\b(?![\w\/\-])(?!\.\d)': 'dd-mm-yyyy',
        r'(?<![\w\/\.\-])(?<!\d\.)\b[12]\d{3}-\d{1,2}-\d{1,2}\b(?![\w\/\-])(?!\.\d)': 'yyyy-mm-dd',
        r'(?<![\w\/\.\-])(?<!\d\.)\d{1,2}\.\d{1,2}\.[12]\d{3}\b(?![\w\/\-])(?!\.\d)': 'dd.mm.yyyy',
        r'(?<![\w\/\.\-])(?<!\d\.)\b[12]\d{3}\.\d{1,2}\.\d{1,2}\b(?![\w\/\-])(?!\.\d)': 'yyyy.mm.dd',
        r'(?<![\w\/\.\-])(?<!\d\.)\b[12]\d{3}\b(?![\w\/\-])(?!\.\d)': 'yyyy',
    }

    doi_patterns = {
        r'doi\.org/10\.\d{4,9}/\S+': 'link',
        r'(?:DOI|doi)\s*:\s*10\.\d{4,9}/\S+': 'citation',
    }

    volume_patterns = {
        r'\d{1,4}\(\d{1,4}(?:-\d{1,4})?\)': '2(14)',
        r'vol\.\s*\d{1,4}': 'vol. 2',
        r'volume[\s\:]*\d{1,4}' : 'volume 2',
        r'\(\d{1,4}\)[\s:]*\d+(?:\s*[-–]\s*\d+)?': '(2):144 - 158' #miks bibtex
    }

    page_range_patterns = {
        r'(?<![\d\.\w])pp\.[\s\:]*\d+(?:\s*[-–]\s*\d+)?': 'pp. 2 - 4',
        r'(?<![\d\.\w])s\.[\s\:]*\d+(?:\s*[-–]\s*\d+)?': 's. 2 - 4',
        r'(?<![\d\.\w])pages?[\s\:]*\d+(?:\s*[-–]\s*\d+)?' :'pages 2 - 4',
        r'(?<![\d\.\w])stron[ya][\s\:]*\d+(?:\s*[-–]\s*\d+)?':'strony 2 - 4',
        r'(?<![\d\.\w])\(\d{1,4}\)[\s:]*\d+(?:\s*[-–]\s*\d+)?': '(2):2 - 4', #mix bibtex
        r'(?<![\w\/\.\-])\d+\s*[-–]\s*\d+(?![\w\/\-])': 'bare 2 - 4' #złapie też inne, może if jeśli nie są inne ewentualnie dodatkowe lookbehind
    }

    access_date_pattern = {
        r'(?<![\d\.\w])[aA]vailable\s+[aA]t[\s:]*' : 'Available at:',
        r'(?<![\d\.\w])\[\s*[oO]nline\s*\]\s*': '[online]',
        r'(?<![\d\.\w])[oO]nline\s*[aA]t[\s\:]*': 'online',
        r'(?<![\d\.\w])[dD]ost[eę]p[\s\:]*': 'dostęp',
        r'(?<![\d\.\w])[dD]ata\s*[dD]ostępu[\s\:]*': 'data dostępu',
        r'(?<![\d\.\w])\(\s*[dD]ata\s*[dD]ostępu[\s\:]*\)': '(data dostępu ...)'
    }

    UPPER_CASE = r'[A-ZĄĆĘŁŃÓŚŹŻÀ-ÖØ-öø-ÿĀ-ž]'
    LOWER_CASE = r'[a-ząćęłńóśźżà-öø-ÿā-ž]'
    special_chars  = rf"[-–']"
    surname_pattern = rf'{UPPER_CASE}{LOWER_CASE}+(?:{special_chars}(?:{UPPER_CASE}|{LOWER_CASE})+)*'
    fullname_pattern = rf'{UPPER_CASE}{LOWER_CASE}+'
    short_name_pattern = rf'{UPPER_CASE}\.'

    author_patterns = {
        rf'{short_name_pattern}(?:\s*{short_name_pattern})*\s{surname_pattern}': 'J. Nowak',
        rf'{fullname_pattern}(?:\s{fullname_pattern})*\s{surname_pattern}': 'Jan Nowak',
        rf'{surname_pattern},\s{short_name_pattern}(?:\s*{short_name_pattern})*': 'Nowak, J.',
        rf'{surname_pattern},\s{fullname_pattern}(?:\s{fullname_pattern})*': 'Nowak, Jan',
    }

    
    #check_quotes
    #check_illiadic
    #check_title
   

    bib_context = Bibliography_context(block_id=0) 
    
    for block_ctx in blocks:
        block = block_ctx.block if hasattr(block_ctx, 'block') else block_ctx
        text = getattr(block, 'full_text', getattr(block, 'content', getattr(block_ctx, 'contents', '')))
        
        bib_item = Bib_item_context(
            content=text,
            authors=None,
            date=None,
            title=None,
            is_title_italics=False,
            book_title=None,
            pages=None,
            publisher=None,
            doi=None,
            volume=None,
            access_date=None,
            url=None,
            online=False,
            journal=None,
            issue=None,
            entry_type=None,
            other=text,
            bibtex_type=None,
            author_format='',
            separator='',
            item=block
        )

        for pattern, fmt in date_patterns.items():
            match = re.search(pattern, bib_item.other)
            if match:
                bib_item.date = match.group(0)
                bib_item.other = bib_item.other.replace(bib_item.date, '').strip()
                break

        for pattern, fmt in author_patterns.items():
            match = re.search(pattern, bib_item.other)
            if match:
                bib_item.authors = match.group(0)
                bib_item.author_format = fmt
                bib_item.other = bib_item.other.replace(bib_item.authors, '').strip()
                break

        for pattern, fmt in page_range_patterns.items():
            match = re.search(pattern, bib_item.other)
            if match:
                bib_item.pages = match.group(0)
                bib_item.other = bib_item.other.replace(bib_item.pages, '').strip()
                break

        for pattern, fmt in volume_patterns.items():
            match = re.search(pattern, bib_item.other)
            if match:
                bib_item.volume = match.group(0)
                bib_item.other = bib_item.other.replace(bib_item.volume, '').strip()
                break

        for pattern, fmt in access_date_pattern.items():
            match = re.search(pattern, bib_item.other)
            if match:
                bib_item.access_date = match.group(0)
                bib_item.online = True
                bib_item.other = bib_item.other.replace(bib_item.access_date, '').strip()
                break

        bib_context.items.append(bib_item)

    matches = check_coherence_iso(blocks, matches, bib_context)
    if producer and re.search(r'latex|tex', producer, re.IGNORECASE):
        matches = check_bibtex(blocks, matches, bib_context)
    
    return matches