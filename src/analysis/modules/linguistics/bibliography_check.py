'''
Skrypt szukający wzorców mogących wskazywać na obecność danego pola w bibliografii: autor, tytuł, url itd.
Głównym celem skryptu jest prędkość (działanie w trybie szybkim), więc przy pomocy regexów i metadanych wpisów bibliograficznych
pola wpisu są heurystyczie dopasowywane do kategorii.
'''

import re
from .linguistics_types import Bibliography_context, Bib_item_context
from .exeptions_check import check_quotes

#TODO przekazać do iso check, access dla samych url i połączyć z date patterns
#zmieniń strukture żeby przekazywać też valueu z dictów, bez case sensivity dla autorów
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

EN_MONTH_LONG =  r'January|February|March|April|May|June|July|August|September|October|November|December'
EN_MONTH_SHORT = r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec'
PL_MONTH_SHORT = r'sty|lut|mar|kwi|maj|czer?|lip|sier?|wrz|paź|list?|gru'
PL_MONTH_LONG = (
    r'stycznia|styczeń|lutego|luty|marca|marzec|kwietnia|kwiecień'
    r'|maja|maj|czerwca|czerwiec|lipca|lipiec|sierpnia|sierpień'
    r'|września|wrzesień|października|październik|listopada|listopad'
    r'|grudnia|grudzień'
)

DATE_PATTERNS = {
    r'(?<![\w\/\.\-])(?<!\d\.)\d{1,2}/\d{1,2}/[12]\d{3}\b(?![\w\/\-])(?!\.\d)': 'dd/mm/yyyy',
    r'(?<![\w\/\.\-])(?<!\d\.)[12]\d{3}/\d{1,2}/\d{1,2}\b(?![\w\/\-])(?!\.\d)': 'yyyy/mm/dd',
    r'(?<![\w\/\.\-])(?<!\d\.)\d{1,2}-\d{1,2}-[12]\d{3}\b(?![\w\/\-])(?!\.\d)': 'dd-mm-yyyy',
    r'(?<![\w\/\.\-])(?<!\d\.)\b[12]\d{3}-\d{1,2}-\d{1,2}\b(?![\w\/\-])(?!\.\d)': 'yyyy-mm-dd',
    r'(?<![\w\/\.\-])(?<!\d\.)\d{1,2}\.\d{1,2}\.[12]\d{3}\b(?![\w\/\-])(?!\.\d)': 'dd.mm.yyyy',
    r'(?<![\w\/\.\-])(?<!\d\.)\b[12]\d{3}\.\d{1,2}\.\d{1,2}\b(?![\w\/\-])(?!\.\d)': 'yyyy.mm.dd',
    r'\([12]\d{3}\)(?=[\s\.\:\;\,])': '(yyyy)',
    rf'(?i)(?<!\w)\d{{1,2}}\s+(?:{EN_MONTH_LONG})\s+[12]\d{{3}}\b(?!\.\d)': 'DD Month YYYY',
    rf'(?i)(?<!\w)(?:{EN_MONTH_LONG})\s+\d{{1,2}},?\s+[12]\d{{3}}\b(?!\.\d)': 'Month DD YYYY',
    rf'(?i)(?<!\w)(?:{EN_MONTH_LONG})\s+[12]\d{{3}}\b(?!\.\d)': 'Month YYYY',
    rf'(?i)(?<!\w)\d{{1,2}}\s+(?:{EN_MONTH_SHORT})\.?\s+[12]\d{{3}}\b(?!\.\d)': 'DD Mon YYYY',
    rf'(?i)(?<!\w)(?:{EN_MONTH_SHORT})\.?\s+\d{{1,2}},?\s+[12]\d{{3}}\b(?!\.\d)': 'Mon DD YYYY',
    rf'(?i)(?<!\w)(?:{EN_MONTH_SHORT})\.?\s+[12]\d{{3}}\b(?!\.\d)': 'Mon YYYY',
    rf'(?i)(?<!\w)\d{{1,2}}\s+(?:{PL_MONTH_LONG})\s+[12]\d{{3}}\b(?!\.\d)': 'DD miesiąc YYYY',
    rf'(?i)(?<!\w)(?:{PL_MONTH_LONG})\s+[12]\d{{3}}\b(?!\.\d)': 'miesiąc YYYY',
    rf'(?i)(?<!\w)\d{{1,2}}\s+(?:{PL_MONTH_SHORT})\.?\s+[12]\d{{3}}\b(?!\.\d)': 'DD mies. YYYY',
    rf'(?i)(?<!\w)(?:{PL_MONTH_SHORT})\.?\s+[12]\d{{3}}\b(?!\.\d)': 'mies. YYYY',
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

BARE_YEAR = {
    r'(?:(?<=[,;]\s)|(?<=\.\s)|(?<=\s))\b[12]\d{3}\b(?=[,;:.\s]|$)': 'YYYY'
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
SHORT_NAME_PATTERN = rf'{UPPER_CASE}\.?(?!\w)'
SEPARATOR_PATTERNS = r'(?:\s*(?:,|[Aa]nd\b|[Ii]\b|&)\s*)+'
END_AUTHOR_PATTERNS = r'(?i)\s*(?:et al\.|i inni|i in)\s*'

AUTHOR_PATTERNS = {
    rf'{SHORT_NAME_PATTERN}(?:\s*{SHORT_NAME_PATTERN})*\s{SURNAME_PATTERN}': 'J. Nowak',
    rf'{FULLNAME_PATTERN}(?:\s(?:{FULLNAME_PATTERN}|{SHORT_NAME_PATTERN}))*\s{SURNAME_PATTERN}': 'Jan Nowak',
    rf'{SURNAME_PATTERN},\s{SHORT_NAME_PATTERN}(?:\s*{SHORT_NAME_PATTERN})*': 'Nowak, J.',
    rf'{SURNAME_PATTERN},\s{FULLNAME_PATTERN}(?:\s{FULLNAME_PATTERN})*': 'Nowak, Jan',
    rf'{SURNAME_PATTERN}\s{SHORT_NAME_PATTERN}(?:\s*{SHORT_NAME_PATTERN})*': 'Nowak J.'
}

def check_bibliography(blocks, producer, bibliography_dict):
    matches = []
    authors = bibliography_dict["people"].union(bibliography_dict["organizations"])
    bib_context = Bibliography_context(block_id=0)
    print(authors)
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
                bib_item.url = url.group(0) if url else None

                authors_text, author_fmt, start_idx, authors_end = extract_authors(masked, content, authors)
                if authors_text is not None:
                    bib_item.authors = authors_text
                    bib_item.author_format = author_fmt

                masked_spans = excluded[:]
                if url_span:
                    masked_spans.append(url_span)
                for field_span in fields.values():
                    masked_spans.append(field_span[:2])
                if authors_text is not None:
                    masked_spans.append((start_idx, authors_end))
                remaining = mask_spans(content, masked_spans)

                plain_candidates = find_title_candidates(remaining)

                bib_item.title, bib_item.publisher, bib_item.is_title_italics = extract_title(content, font_spans, quoted_spans, plain_candidates, authors_end)

                if 'date' in fields:
                    bib_item.date = fields['date'][2]

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
                    bib_item.online = True

                if 'doi' in fields:
                    bib_item.doi = fields['doi'][2]

                if 'end_key' in fields:
                    _, in_end, _ = fields['end_key']
                    post_in_anchors = sorted(
                        start for field_name, (start, end, val) in fields.items()
                        if field_name != 'end_key' and start > in_end
                    )
                    book_title_end = post_in_anchors[0] if post_in_anchors else len(content)
                    bib_item.publisher = content[in_end:book_title_end].strip(' .,;') #TODO dict z tego

                for val in (bib_item.title, bib_item.publisher):
                    if val:
                        pos = remaining.find(val)
                        if pos >= 0:
                            remaining = mask_spans(remaining, [(pos, pos + len(val))])
                bib_item.other = re.sub(r'\s+', ' ', remaining).strip()

                if bib_item.title and not any(c.isalpha() for c in bib_item.title):
                    bib_item.title = None
                if bib_item.publisher and not any(c.isalpha() for c in bib_item.publisher):
                    bib_item.publisher = None
                if bib_item.authors and not any(c.isalpha() for c in bib_item.authors):
                    bib_item.authors = None

                bib_context.items.append(bib_item)

                print(
                f"  content: {content}\n"
                f"  authors: {bib_item.authors}\n"
                f"{bib_item.author_format}\n"
                f"  title: {bib_item.title}\n"
                f"  publisher : {bib_item.publisher}\n"
                f"  date : {bib_item.date}\n"
                f"  access_date: {bib_item.access_date}\n"
                f"  pages: {bib_item.pages}\n"
                f"  volume: {bib_item.volume}\n"
                f"  url: {bib_item.url}\n"
                f"  doi: {bib_item.doi}\n"
                f"  other: {bib_item.other}\n"
            )
       # matches = check_coherence_iso(blocks, matches, bib_context)
       # if producer and re.search(r'latex|tex', producer, re.IGNORECASE):
        #    matches = check_bibtex(blocks, matches, bib_context)
        matches = []
        bib_matches = []
    return matches, bib_matches


def first_match(content, patterns):
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.start(), match.end(), match.group(0)
    return None


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

    result = first_match(content, DATE_PATTERNS)
    if result:
        found['date'] = result

    result = first_match(content, PAGES_PATTERNS)
    if result:
        found['pages'] = result

    result = ART_INTRO_KEYWORDS.search(content)
    if result:
        found['end_key'] = (result.start(), result.end(), result.group(0))

    result = first_match(content, VOLUME_PATTERNS)
    if result:
        found['volume'] = result

    # bare daty i volumes jako ostatnie, aby ograniczyć FP
    if 'date' not in found:
        result = first_match(content, BARE_YEAR)
        if result:
            found['date'] = result

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
    best_known = None
    best_other = None
    best_fallback = None

    for pattern, fmt in AUTHOR_PATTERNS.items():
        match = re.search(pattern, masked)
        if match and not check_quotes(match.start(), match.end(), content):
            candidate = (match.end(), match.start(), fmt, pattern)
            if fmt == 'Jan Nowak':
                if match.group(0).strip() in authors:
                    if best_known is None or match.end() < best_known[0]:
                        best_known = candidate
                else:
                    if best_fallback is None or match.end() < best_fallback[0]:
                        best_fallback = candidate
            else:
                if best_other is None or match.end() > best_other[0]:
                    best_other = candidate

    winner = best_known or best_other or best_fallback
    if winner is None:
        return None, '', 0, 0

    idx, start_idx, author_fmt, author_pattern = winner
    current_idx = idx
    authors_end = idx
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
    is_title_italics = False
    not_keyword = True
    publisher_span = None
    if not_keyword:
        for _, start, end in italic_after:
            if any(keyword in content[start:end].lower() for keyword in keywords):
                publisher_span = (start, end)
                not_keyword = False
                break
    if not_keyword:
        for start, end in quoted_after:
            if any(keyword in content[start:end].lower() for keyword in keywords):
                publisher_span = (start, end)
                not_keyword = False
                break
    if not_keyword:
        for candidate in plain_candidates:
            if any(keyword in candidate[0].lower() for keyword in keywords):
                publisher_span = (candidate[2], candidate[2] + len(candidate[0]))
                not_keyword = False
                break
    if publisher_span:
        publisher = content[publisher_span[0]:publisher_span[1]]
        if has_quoted:
            title = content[quoted_after[0][0]:quoted_after[0][1]].strip(quotes_types)
        elif has_italic:
            title = content[italic_after[0][1]:italic_after[0][2]]
        elif plain_candidates:
            title = plain_candidates[0][0]
    elif has_italic and has_quoted:
        quote_start = quoted_after[0][0]
        italic_start = italic_after[0][1]
        if quote_start < italic_start:
            title = content[quote_start:quoted_after[0][1]].strip(quotes_types)
            publisher = content[italic_after[0][1]:italic_after[0][2]]
        else:
            title = content[italic_after[0][1]:italic_after[0][2]]
            is_title_italics = italic_after[0][0] == 'italic'
            publisher = content[quoted_after[0][0]:quoted_after[0][1]].strip(quotes_types)
    elif has_quoted:
        quote_end = quoted_after[0][1]
        title = content[quoted_after[0][0]:quote_end].strip(quotes_types)
        plain_after = [seg for seg, _, idx in plain_candidates if idx > quote_end]
        if plain_after:
            publisher = plain_after[0]
    elif has_italic and plain_candidates:
        title = plain_candidates[0][0]
        publisher = content[italic_after[0][1]:italic_after[0][2]]
    elif has_italic:
        title = content[italic_after[0][1]:italic_after[0][2]]
        is_title_italics = italic_after[0][0] == 'italic'
    elif plain_candidates:
        title = plain_candidates[0][0]
        if len(plain_candidates) > 1:
            publisher = plain_candidates[1][0]

    return title, publisher, is_title_italics


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
