'''
Skrypt szukający wzorców mogących wskazywać na obecność danego pola w bibliografii: autor, tytuł, url itd.
Głównym celem skryptu jest prędkość (działanie w trybie szybkim), więc przy pomocy regexów i metadanych wpisów bibliograficznych
pola wpisu są heurystyczie dopasowywane do kategorii.
'''

import re
from .linguistics_types import Bibliography_context, Bib_item_context
from .exeptions_check import check_quotes
from .iso_and_bibtex_check import check_coherence_iso, check_bibtex

LINKER_KEYWORDS = {
    'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but',
    'w', 'i', 'z', 'dla', 'do', 'na', 'od', 'po', 'ze', 'że', 'oraz', 'by'}

ARTICLE_KEYWORDS = {'journal', 'conference', 'konferencja', 'review', 'proceedings', 'briefings', 'monthly', 'annual', 'magazine', 'czasopismo', 'miesięcznik'}
BOOK_KEYWORDS = {'wyd', 'wydawnictwo', 'press', 'pwn', 'publishing', 'publishers', 'pub', 'ieee'}
ART_INTRO_KEYWORDS = re.compile(r'\s+(?:[Ii]n|[Ww])\.?:\s+')

DOI_PATTERNS = {
    r'doi\.org/10\.\d{4,9}/\S+': 'link',
    r'(?:DOI|doi)\s*:\s*10\.\d{4,9}/\S+': 'citation',
}

ACCESS_PATTERNS = {
    r'(?<![\d\.\w])[aA]vailable\s+[aA]t[\s:]*': 'Available at:',
    r'(?<![\d\.\w])[aA]vailable\s+[\s:]*': 'Available:',
    r'(?<![\d\.\w])\[\s*[oO]nline\s*\]\s*': '[online]',
    r'(?<![\d\.\w])[oO]nline\s*(?:[aA]t)[\s\:]*': 'online at',
    r'(?<![\d\.\w])\(\s*[dD]ata\s*[dD]ostępu[\s\:]*\)': '(data dostępu)',
    r'(?<![\d\.\w])[dD]ata\s*[dD]ostępu[\s\:]*': 'data dostępu',
    r'(?<![\d\.\w])[dD]ost[eę]p[\s\:]*': 'dostęp',
}

EN_MONTH_LONG = r'January|February|March|April|May|June|July|August|September|October|November|December'
EN_MONTH_SHORT = r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec'
PL_MONTH_SHORT = r'sty|lut|mar|kwi|maj|czer?|lip|sier?|wrz|paź|list?|grud?'
PL_MONTH_LONG = (
    r'stycznia|styczeń|lutego|luty|marca|marzec|kwietnia|kwiecień'
    r'|maja|maj|czerwca|czerwiec|lipca|lipiec|sierpnia|sierpień'
    r'|września|wrzesień|października|październik|listopada|listopad'
    r'|grudnia|grudzień'
)
R_PATTERN = rf'(?:\s*[rR]\.?)?'
YEAR_PATTERN = rf'(?:1[6789]\d{{2}}|2[01]\d{{2}}){R_PATTERN}'
DATE_PATTERNS = {
    rf'(?i)(?<!\w)\d{{1,2}}\s+(?:{EN_MONTH_LONG})\s+{YEAR_PATTERN}\b(?!\.\d)': 'DD Month YYYY',
    rf'(?i)(?<!\w)(?:{EN_MONTH_LONG})\s+\d{{1,2}},?\s+{YEAR_PATTERN}\b(?!\.\d)': 'Month DD YYYY',
    rf'(?i)(?<!\w)(?:{EN_MONTH_LONG})\s+{YEAR_PATTERN}\b(?!\.\d)': 'Month YYYY',
    rf'(?i)(?<!\w)\d{{1,2}}\s+(?:{EN_MONTH_SHORT})\.?\s+{YEAR_PATTERN}\b(?!\.\d)': 'DD Mon YYYY',
    rf'(?i)(?<!\w)(?:{EN_MONTH_SHORT})\.?\s+\d{{1,2}},?\s+{YEAR_PATTERN}\b(?!\.\d)': 'Mon DD YYYY',
    rf'(?i)(?<!\w)(?:{EN_MONTH_SHORT})\.?\s+{YEAR_PATTERN}\b(?!\.\d)': 'Mon YYYY',
    rf'(?i)(?<!\w)\d{{1,2}}\s+(?:{PL_MONTH_LONG})\s+{YEAR_PATTERN}\b(?!\.\d)': 'DD miesiąc YYYY',
    rf'(?i)(?<!\w)(?:{PL_MONTH_LONG})\s+{YEAR_PATTERN}\b(?!\.\d)': 'miesiąc YYYY',
    rf'(?i)(?<!\w)\d{{1,2}}\s+(?:{PL_MONTH_SHORT})\.?\s+{YEAR_PATTERN}\b(?!\.\d)': 'DD mies. YYYY',
    rf'(?i)(?<!\w)(?:{PL_MONTH_SHORT})\.?\s+{YEAR_PATTERN}\b(?!\.\d)': 'mies. YYYY',
    rf'(?<![\w\/\.\-])(?<!\d\.)\d{{1,2}}/\d{{1,2}}/{YEAR_PATTERN}\b(?![\w\/\-])(?!\.\d)': 'dd/mm/yyyy',
    rf'(?<![\w\/\.\-])(?<!\d\.){YEAR_PATTERN}/\d{{1,2}}/\d{{1,2}}\b(?![\w\/\-])(?!\.\d)': 'yyyy/mm/dd',
    rf'(?i)(?<![\w\/\.\-])(?<!\d\.)\d{{1,2}}-{PL_MONTH_LONG}-{YEAR_PATTERN}\b(?![\w\/\-])(?!\.\d)': 'dd-Miesiąc-yyyy',
    rf'(?i)(?<![\w\/\.\-])(?<!\d\.)\d{{1,2}}-{PL_MONTH_SHORT}-{YEAR_PATTERN}\b(?![\w\/\-])(?!\.\d)': 'dd-mie-yyyy',
    rf'(?i)(?<![\w\/\.\-])(?<!\d\.)\d{{1,2}}-{EN_MONTH_LONG}-{YEAR_PATTERN}\b(?![\w\/\-])(?!\.\d)': 'dd-Month-yyyy',
    rf'(?i)(?<![\w\/\.\-])(?<!\d\.)\d{{1,2}}-{EN_MONTH_SHORT}-{YEAR_PATTERN}\b(?![\w\/\-])(?!\.\d)': 'dd-mon-yyyy',
    rf'(?<![\w\/\.\-])(?<!\d\.)\d{{1,2}}-\d{{1,2}}-{YEAR_PATTERN}\b(?![\w\/\-])(?!\.\d)': 'dd-mm-yyyy',
    rf'(?<![\w\/\.\-])(?<!\d\.)\b{YEAR_PATTERN}-\d{{1,2}}-\d{{1,2}}\b(?![\w\/\-])(?!\.\d)': 'yyyy-mm-dd',
    rf'(?<![\w\/\.\-])(?<!\d\.)\d{{1,2}}\.\d{{1,2}}\.{YEAR_PATTERN}\b(?![\w\/\-])(?!\.\d)': 'dd.mm.yyyy',
    rf'(?<![\w\/\.\-])(?<!\d\.)\b{YEAR_PATTERN}\.\d{{1,2}}\.\d{{1,2}}\b(?![\w\/\-])(?!\.\d)': 'yyyy.mm.dd',
    rf'\({YEAR_PATTERN}\)(?=[\s\.\:\;\,])': '(yyyy)',
    rf'(?:(?<=[,;]\s)|(?<=\.\s)|(?<=\s))\b{YEAR_PATTERN}\b(?=[,;:.\s]|$)(?!\.[\d\w])': 'YYYY'
}


PAGES_PATTERNS = {
    r'(?<![\d\.\w])pp\.[\s\:]*\d+(?:\s*[-–]\s*\d+)?': 'pp. 2 - 4',
    r'(?<![\d\.\w])s\.[\s\:]*\d+(?:\s*[-–]\s*\d+)?': 's. 2 - 4',
    r'(?<![\d\.\w])pages?[\s\:]*\d+(?:\s*[-–]\s*\d+)?': 'pages 2 - 4',
    r'(?<![\d\.\w])stron[ya][\s\:]*\d+(?:\s*[-–]\s*\d+)?': 'strony 2 - 4',
    r'(?<![\d\.\w])\(\d{1,4}\)[\s:]*\d+(?:\s*[-–]\s*\d+)?': '(2):2 - 4',  #mix bibtex
}

VOLUME_PATTERNS = {
    r'\d{1,4}\(\d{1,4}(?:-\d{1,4})?\)': '2(14)',
    r'vol\.\s*\d{1,4}': 'vol. 2',
    r'volume[\s\:]*\d{1,4}': 'volume 2',
    r'\(\d{1,4}\)[\s:]*\d+(?:\s*[-–]\s*\d+)?': '(2):144 - 158',  #miks bibtex
}

BARE_VOLUME = {
    r'\d{1,4}\(\d{1,4}(?:-\d{1,4})?\)': '2(14)',
    r'\(\d{1,4}\)[\s:]*\d+(?:\s*[-–]\s*\d+)?': '(2):144 - 158',  #miks bibtex
}

BARE_PAGES = { r'(?<![\w\/\.\-])\d+\s*[-–]\s*\d+(?![\w\/\-])': 'bare 2 - 4',}
URL_PATTERN = re.compile(r'https?://\S+')

UPPER_CASE = r'[A-ZĄĆĘŁŃÓŚŹŻÀ-ÖØ-öø-ÿĀ-ž]'
LOWER_CASE = r'[a-ząćęłńóśźżà-öø-ÿā-ž]'
SPECIAL_CHARS = rf"[-–']"
SURNAME_PATTERN = rf'{UPPER_CASE}{LOWER_CASE}+(?:{SPECIAL_CHARS}(?:{UPPER_CASE}|{LOWER_CASE})+)*'
FULLNAME_PATTERN = rf'{UPPER_CASE}{LOWER_CASE}+'
SHORT_NAME_PATTERN = rf'(?<!\w){UPPER_CASE}\.?(?!\w)'
SEPARATOR_PATTERNS = r'(?:\s*(?:,|[Aa]nd\b|[Ii]\b|&)\s*)+'
END_AUTHOR_PATTERNS = r'(?i)\s*(?:et al\.|i inni|i in)\s*'

AUTHOR_PATTERNS = {
    rf'{SHORT_NAME_PATTERN}(?:\s*{SHORT_NAME_PATTERN})*\s{SURNAME_PATTERN}': 'J. Nowak',
    rf'{FULLNAME_PATTERN}(?:\s(?:{FULLNAME_PATTERN}|{SHORT_NAME_PATTERN}))*\s{SURNAME_PATTERN}': 'Jan Nowak',
    rf'{SURNAME_PATTERN},\s{SHORT_NAME_PATTERN}(?:\s*{SHORT_NAME_PATTERN})*\s*': 'Nowak, J.',
    rf'{SURNAME_PATTERN},\s{FULLNAME_PATTERN}(?:\s(?:{FULLNAME_PATTERN}|{SHORT_NAME_PATTERN}))*': 'Nowak, Jan',
    rf'{SURNAME_PATTERN}\s{SHORT_NAME_PATTERN}(?:\s*{SHORT_NAME_PATTERN})*': 'Nowak J.'
}

def check_bibliography(blocks, producer, bibliography_dict, bibtex_check_bool = True):
    matches = []
    authors = bibliography_dict["people"].union(bibliography_dict["organizations"])
    bib_context = Bibliography_context(block_id=0)
    for block in blocks:
        if block.block.type == "list" and block.block.is_bibliography:
            bib_context.block_id = block.block.block_id

            for list_item in block.block.items:
                content = list_item.text

                bib_item = Bib_item_context(
                    content=content,
                    item=list_item)

                font_spans = collect_font_spans(list_item)
                quoted_spans = check_quotes(0, 0, content, return_spans=True)

                excluded = [(start, end) for _, start, end in font_spans] + quoted_spans
                masked = mask_spans(content, excluded)
                fields = extract_fields(masked)
                url = URL_PATTERN.search(masked)
                url_span = (url.start(), url.end()) if url else None
                bib_item.url = {url.group(0): 'url'} if url else None

                authors_text, author_fmt, start_idx, authors_end = extract_authors(masked, content, authors)
                if authors_text is not None:
                    bib_item.authors = {authors_text: author_fmt}

                masked_spans = excluded[:]
                if url_span:
                    masked_spans.append(url_span)
                for field_name, field_span in fields.items():
                    if field_name != 'date':
                        masked_spans.append(field_span[:2])
                if authors_text is not None:
                    masked_spans.append((start_idx, authors_end))
                remaining = mask_spans(content, masked_spans)

                plain_candidates = find_title_candidates(remaining)

                bib_item.title, bib_item.publisher = extract_title(content, font_spans, quoted_spans, plain_candidates, authors_end)

                if 'date' in fields:
                    bib_item.date = fields['date']

                if 'pages' in fields:
                    bib_item.pages = fields['pages'][2]
                elif 'volume_extra' not in fields:
                    result = first_match(masked, BARE_PAGES)
                    if result:
                        bib_item.pages = result[2]

                if 'volume' in fields:
                    bib_item.volume = fields['volume'][2]
                elif 'volume_extra' in fields:
                    bib_item.volume = fields['volume_extra'][2]

                if 'access_date' in fields:
                    bib_item.access_date = fields['access_date'][2]
                    #bib_item.online = True
                    bib_item.online = bool(url_span)

                if 'doi' in fields:
                    bib_item.doi = fields['doi'][2]

                for val in (bib_item.title, bib_item.publisher):
                    if val:
                        for text in val:
                            pos = remaining.find(text)
                            if pos >= 0:
                                remaining = mask_spans(remaining, [(pos, pos + len(text))])
                other_text = re.sub(r'\s+', ' ', remaining).strip()
                if other_text:
                    bib_item.other = other_text

                if bib_item.title and not any(c.isalpha() for text in bib_item.title for c in text):
                    bib_item.title = None
                if bib_item.publisher and not any(c.isalpha() for text in bib_item.publisher for c in text):
                    bib_item.publisher = None
                if bib_item.authors and not any(c.isalpha() for text in bib_item.authors for c in text):
                    bib_item.authors = None

                bib_context.items.append(bib_item)
    bib_blocks = {}
    for block in blocks:
        if block.block.type == "list" and block.block.is_bibliography:
            for list_item in block.block.items:
                bib_blocks[list_item.item_id] = block.block

    matches = check_coherence_iso(matches, bib_context, bib_blocks)
    if producer and re.search(r'latex|tex', producer, re.IGNORECASE) and bibtex_check_bool:
        matches.extend(check_bibtex(matches, bib_context, bib_blocks))
    return matches

def first_match(content, patterns):
    for pattern, name in patterns.items():
        match = re.search(pattern, content)
        if match:
            return match.start(), match.end(), {match.group(0): name}
    return None

def all_date_matches(content, date_patterns):
    results = []
    covered = []
    for pattern, name in date_patterns.items():
        for match in re.finditer(pattern, content):
            if not any(start <= match.start() < end for start, end in covered):
                results.append({match.group(0): name})
                covered.append((match.start(), match.end()))
                if len(results) > 2:
                    return results
    return results


def collect_font_spans(list_item):
    spans = []
    italic= None
    for word in list_item.words[1:]:  # words[0] to wg ekstraktora redakcji marker
        if word.italic:
            italic = italic or [word.start_char, word.end_char]
            italic[1] = word.end_char
        elif italic:
            spans.append(('italic', italic[0], italic[1]))
            italic = None
    if italic:
        spans.append(('italic', italic[0], italic[1]))
    return spans


def extract_fields(content):
    found = {}

    result = first_match(content, DOI_PATTERNS)
    if result:
        found['doi'] = result

    result = first_match(content, ACCESS_PATTERNS)
    if result:
        found['access_date'] = result

    dates = all_date_matches(content, DATE_PATTERNS)
    if dates:
        found['date'] = dates

    result = first_match(content, PAGES_PATTERNS)
    if result:
        found['pages'] = result

    result = first_match(content, VOLUME_PATTERNS)
    if result:
        found['volume'] = result

    if 'volume' not in found:
        result = first_match(content, BARE_VOLUME)
        if result:
            found['volume_extra'] = result

    return found


def mask_spans(content, spans):
    if not spans:
        return content
    content_list = list(content)
    for start, end in spans:
        for i in range(max(0, start), min(end, len(content_list))):
            content_list[i] = ' '
    return ''.join(content_list)


def extract_authors(masked, content, authors):
    best_start_known = None
    best_start_other = None
    best_start_fallback = None
    best_known = None
    best_other = None
    best_fallback = None

    authors_lower = {a.lower() for a in authors}

    for pattern, fmt in AUTHOR_PATTERNS.items():
        match = re.search(pattern, masked)
        if match and not check_quotes(match.start(), match.end(), content):
            candidate = (match.end(), match.start(), fmt, pattern)
            if fmt == 'Jan Nowak':
                in_authors = match.group(0).strip().lower() in authors_lower
                if match.start() == 0:
                    if in_authors:
                        best_start_known = candidate
                    else:
                        best_start_fallback = candidate
                else:
                    if in_authors:
                        if best_known is None or match.end() < best_known[0]:
                            best_known = candidate
                    else:
                        if best_fallback is None or match.end() < best_fallback[0]:
                            best_fallback = candidate
            else:
                if match.start() == 0:
                    if best_start_other is None or match.end() > best_start_other[0]:
                        best_start_other = candidate
                else:
                    if best_other is None or match.end() > best_other[0]:
                        best_other = candidate

    best_direct = None
    if not (best_start_known or best_start_other or best_start_fallback):
        for author in authors:
            if masked.lower().startswith(author.lower()):
                best_direct = (len(author), 0, 'different', None)
                break

    winner = best_start_known or best_start_other or best_start_fallback or best_direct or best_known or best_other or best_fallback
    if winner is None:
        return None, '', 0, 0

    idx, start_idx, author_fmt, author_pattern = winner
    current_idx = idx
    authors_end = idx

    if author_fmt == 'different':
        while True:
            current_text = masked[current_idx:]
            if re.match(END_AUTHOR_PATTERNS, current_text):
                break
            sep = re.match(SEPARATOR_PATTERNS, current_text)
            if not sep:
                break
            rest = masked[current_idx + sep.end():]
            next_known = next((a for a in authors if rest.lower().startswith(a.lower())), None)
            if next_known:
                current_idx += sep.end() + len(next_known)
                authors_end = current_idx
            else:
                break
    else:
        while True:
            current_text = masked[current_idx:]
            if re.match(END_AUTHOR_PATTERNS, current_text):
                break
            separator = re.match(SEPARATOR_PATTERNS, current_text)
            if separator:
                current_idx += separator.end()
                current_text = masked[current_idx:]
            next_author = re.match(author_pattern, current_text)
            if next_author:
                current_idx += next_author.end()
                authors_end = current_idx
            else:
                break

    return content[start_idx:authors_end], author_fmt, start_idx, authors_end


def extract_title(content, font_spans, quoted_spans, plain_candidates, authors_end):
    italic_after = [(style, start, end) for style, start, end in font_spans if start >= authors_end]
    quoted_after = [(start, end) for start, end in quoted_spans if start >= authors_end]
    has_italic = bool(italic_after)
    has_quoted = bool(quoted_after)
    quotes_types = '"„″""\''
    keywords = BOOK_KEYWORDS.union(ARTICLE_KEYWORDS)
    title = None
    publisher = None
    not_keyword = True
    publisher_span = None
    publisher_template = None
    if not_keyword:
        for _, start, end in italic_after:
            if any(keyword in content[start:end].lower() for keyword in keywords):
                publisher_span = (start, end)
                publisher_template = 'italic'
                not_keyword = False
                break
    if not_keyword:
        for start, end in quoted_after:
            if any(keyword in content[start:end].lower() for keyword in keywords):
                publisher_span = (start, end)
                publisher_template = 'quotes'
                not_keyword = False
                break
    if not_keyword:
        for candidate in plain_candidates:
            if any(keyword in candidate[0].lower() for keyword in keywords):
                publisher_span = (candidate[2], candidate[2] + len(candidate[0]))
                publisher_template = candidate[1][0]
                not_keyword = False
                break
    if publisher_span:
        publisher = {content[publisher_span[0]:publisher_span[1]]: publisher_template}
        quoted_title = [(start, end) for start, end in quoted_after if (start, end) != publisher_span]
        italic_title = [(style, start, end) for style, start, end in italic_after if (start, end) != publisher_span]
        plain_title = [candidate for candidate in plain_candidates if candidate[2] != publisher_span[0]]
        if quoted_title:
            title = {content[quoted_title[0][0]:quoted_title[0][1]].strip(quotes_types): 'quotes'}
        elif italic_title:
            title = {content[italic_title[0][1]:italic_title[0][2]]: 'italic'}
        elif plain_title:
            title = {plain_title[0][0]: plain_title[0][1][0]}
    elif has_italic and has_quoted:
        quote_start = quoted_after[0][0]
        italic_start = italic_after[0][1]
        if quote_start < italic_start:
            title = {content[quote_start:quoted_after[0][1]].strip(quotes_types): 'quotes'}
            publisher = {content[italic_after[0][1]:italic_after[0][2]]: 'italic'}
        else:
            title = {content[italic_after[0][1]:italic_after[0][2]]: 'italic'}
            publisher = {content[quoted_after[0][0]:quoted_after[0][1]].strip(quotes_types): 'quotes'}
    elif has_quoted:
        quote_end = quoted_after[0][1]
        title = {content[quoted_after[0][0]:quote_end].strip(quotes_types): 'quotes'}
        plain_after = [(seg, pattern) for seg, pattern, idx in plain_candidates if idx > quote_end]
        if plain_after:
            publisher = {plain_after[0][0]: plain_after[0][1][0]}
    elif has_italic and plain_candidates:
        title = {plain_candidates[0][0]: plain_candidates[0][1][0]}
        publisher = {content[italic_after[0][1]:italic_after[0][2]]: 'italic'}
    elif has_italic:
        title = {content[italic_after[0][1]:italic_after[0][2]]: 'italic'}
    elif plain_candidates:
        sep = ART_INTRO_KEYWORDS.search(content)
        if sep:
            before = [candidate for candidate in plain_candidates if candidate[2] + len(candidate[0]) <= sep.start()]
            after = [candidate for candidate in plain_candidates if candidate[2] >= sep.end()]
            if before:
                title = {before[0][0]: before[0][1][0]}
            if after:
                publisher = {after[0][0]: after[0][1][0]}
        else:
            title = {plain_candidates[0][0]: plain_candidates[0][1][0]}
            if len(plain_candidates) > 1:
                publisher = {plain_candidates[1][0]: plain_candidates[1][1][0]}

    return title, publisher


def find_title_candidates(text):
    results = []
    idx = 0
    for chunk in re.split(r'(\s{2,})', text):
        if re.fullmatch(r'\s{2,}', chunk):
            idx += len(chunk)
            continue
        seg_idx = idx
        idx += len(chunk)
        seg = chunk.strip(' .,;:')
        if len(seg) < 4:
            continue
        cand_words = re.findall(r'\b[^\W\d_]+\b', seg)
        if len(cand_words) < 2 or not cand_words[0][:1].isupper():
            continue
        rest = [w for w in cand_words[1:] if w.lower() not in LINKER_KEYWORDS]
        if not rest:
            continue
        lower_count = sum(1 for word in rest if word[:1].islower())
        upper_count = sum(1 for word in rest if word[:1].isupper())
        pattern = []
        if lower_count > 0 and lower_count >= upper_count:
            pattern.append('sentence_case')
        elif upper_count > 0 and upper_count > lower_count:
            pattern.append('title_case')
        if pattern:
            results.append((seg, pattern, seg_idx))
    return results
