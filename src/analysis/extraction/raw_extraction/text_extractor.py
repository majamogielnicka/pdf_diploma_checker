from typing import Dict
import re

from analysis.extraction.raw_extraction.bare_struct import (
    TextBlock,
    TextLine,
    TextSpan,
)
from analysis.extraction.raw_extraction.geometry import (
    calculate_margins,
    line_spacing,
    check_page_format,
    is_footer,
    analyze_line_alignment,
)

def fix_latex(text):
    replace = {  # Słownik znaków do podmiany.
        "´s": "ś",
        "´S": "Ś",
        "´c": "ć",
        "´C": "Ć",
        "´z": "ź",
        "´Z": "Ź",
        "˙z": "ż",
        "˙Z": "Ż",
        "´n": "ń",
        "´N": "Ń",
        "´o": "ó",
        "´O": "Ó",
        "˛a": "ą",
        "˛A": "Ą",
        "˛e": "ę",
        "˛E": "Ę",
        "ﬀ": "ff",
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "ﬅ": "ft",
        "ﬆ": "st",
    }
    for wrong, right in replace.items():
        text = text.replace(wrong, right)
    return text

# Niestety używanie samego dicta powoduje, że nie można dokładnie rozdzielić spanów na same słowa z informacją
# o ich położeniu. Natomiast sama lista słów zwraca dokładne koordynaty słowa, ale nie pozwala na
# detekcję czcionki, itd. W związku z tym użyto zarówno dicta jak i listy słów, aby połączyć korzyści.
def parse_text_block(
    raw_block: dict,
    word_list: list,
    page_width: float,
    margins: Dict[str, float],
    last_block_btmline: float,
    current_span_id: int,
    all_spacings: list,
    is_ftr: bool,
) -> tuple[TextBlock, float, int]:
    lines = []
    block_words = []
    prev_bottomline = last_block_btmline

    # Sprawdzanie, które słowa są w środk danego bloku, żeby nie sprawdzać każdego słowa
    # na stronie czy nie należy do danego spana

    for x in word_list:
        if x[5] == raw_block["number"]:
            block_words.append(x)

    # Lista użytych słów, żeby nie powielać słowa
    used_words = set()

    for raw_line in raw_block["lines"]:
        spans = []
        max_font_size = 0.0  # Do znalezienia słowa o największej czcionce w linijce.

        for raw_span in raw_line["spans"]:
            if not raw_span["text"].strip():
                continue

            s_bbox = raw_span["bbox"]
            span_words = []

            if raw_span["size"] > max_font_size:
                max_font_size = raw_span["size"]

            for x in block_words:
                if x in used_words:
                    continue

                # Zmienne przydatne do łatki na ucinanie słów przy nawiasach, cudzysłowach, itp.
                word_text = x[4]
                m_left = 0.2
                m_right = 0.2
                punctuation = (
                    "(",
                    ")",
                    "[",
                    "]",
                    "{",
                    "}",
                    '"',
                    "'",
                    "”",
                    "„",
                    ".",
                    ",",
                    ":",
                    ";",
                    "?",
                    "!",
                    "-",
                )

                if word_text and word_text[0] in punctuation:
                    m_left = 15.0

                if word_text and word_text[-1] in punctuation:
                    m_right = 15.0
                # Sprawdzanie czy dane słowo należy do spanu z małym marginesem błędu (0.2), w razie
                # problemów można zwiększyć
                # Dodatkowo, jeśli słowo zaczyna się lub kończy interpunkcją, to zwiększamy margines, żeby zapobiec ucinaniu słów przy nawiasach, cudzysłowach, itp.
                if (
                    x[0] >= s_bbox[0] - m_left
                    and x[1] >= s_bbox[1] - 1.0
                    and x[2] <= s_bbox[2] + m_right
                    and x[3] <= s_bbox[3] + 1.0
                ):
                    span_words.append(x)
                    used_words.add(x)

            # obsluga flag
            flags = raw_span["flags"]

            if span_words:
                raw_text_stripped = raw_span["text"].strip()

                first_word_text = span_words[0][4]
                last_word_text = span_words[-1][4]

                missing_start = ""
                missing_end = ""

                start_match = re.match(r'^([(),.;:!?\[\]\{\}"”„]+)', raw_text_stripped)
                end_match = re.search(r'([(),.;:!?\[\]\{\}"”„]+)$', raw_text_stripped)

                if start_match and not first_word_text.startswith(start_match.group(1)):
                    missing_start = start_match.group(1)
                if end_match and not last_word_text.endswith(end_match.group(1)):
                    missing_end = end_match.group(1)

                for idx, orig_x in enumerate(span_words):
                    x = list(orig_x)
                    if idx == 0 and missing_start:
                        is_closing_punct = all(c in ".,;:!?)]}”" for c in missing_start)
                        if is_closing_punct and len(spans) > 0:
                            spans[-1].text += missing_start
                            p_box = spans[-1].bbox
                            spans[-1].bbox = (
                                p_box[0],
                                p_box[1],
                                p_box[2] + 4.0,
                                p_box[3],
                            )
                        else:
                            x[4] = missing_start + x[4]
                            x[0] -= 4.0

                    if idx == len(span_words) - 1 and missing_end:
                        x[4] = x[4] + missing_end
                        x[2] += 4.0

                    current_span_id += 1
                    spans.append(
                        TextSpan(
                            span_id=current_span_id,
                            text=fix_latex(x[4]),
                            font=raw_span["font"],
                            size=round(raw_span["size"], 2),
                            color=raw_span["color"],
                            bold=bool(flags & 16),
                            italic=bool(flags & 2),
                            bbox=(x[0], x[1], x[2], x[3]),
                        )
                    )
            else:
                current_span_id += 1
                spans.append(
                    TextSpan(
                        span_id=current_span_id,
                        text=fix_latex(raw_span["text"]),
                        font=raw_span["font"],
                        size=round(raw_span["size"], 2),
                        color=raw_span["color"],
                        bold=bool(flags & 16),
                        italic=bool(flags & 2),
                        bbox=raw_span["bbox"],
                    )
                )

        if spans:
            spacing = None
            curr_bottomline = raw_line["bbox"][3]
            if prev_bottomline is not None:
                spacing = line_spacing(curr_bottomline, prev_bottomline, max_font_size)
                if not is_ftr:
                    if spacing > 0.5 and spacing < 3.0:
                        all_spacings.append(spacing)
                    else:
                        spacing = None
                else:
                    spacing = None

            curr_line = TextLine(
                spans=spans,
                bbox=raw_line["bbox"],
                baseline=raw_line["wmode"],
                line_spacing=spacing,
            )
            prev_bottomline = curr_bottomline
            # analiza justowania
            alignment, consistent, gap_toright = analyze_line_alignment(
                curr_line, page_width, margins
            )
            curr_line.alignement = alignment
            curr_line.spacing_consistency = consistent
            # curr_line.gap_to_r = gap_toright #debug
            lines.append(curr_line)
    output_block = TextBlock(
        lines=lines,
        bbox=raw_block["bbox"],
        block_id=raw_block["number"],
        block_type="footer" if is_ftr else "text",
    )
    clean_block = post_process_block(output_block)
    # clean_block = output_block
    return clean_block, prev_bottomline, current_span_id


def post_process_block(block: TextBlock) -> TextBlock:
    # Bezpieczna mapa liczbowych kodów Unicode (ogonek, kropka, akcent ostry)
    MAPS = {
        0x02DB: {0x0061: 0x0105, 0x0041: 0x0104, 0x0065: 0x0119, 0x0045: 0x0118},  # ˛
        0x02D9: {0x007A: 0x017C, 0x005A: 0x017B},  # ˙
        0x00B4: {  # ´
            0x0073: 0x015B,
            0x0053: 0x015A,
            0x0063: 0x0107,
            0x0043: 0x0106,
            0x007A: 0x017A,
            0x005A: 0x0179,
            0x006E: 0x0144,
            0x004E: 0x0143,
            0x006F: 0x00F3,
            0x004F: 0x00D3,
        },
    }

    MERGE_TARGETS = {"ą", "Ą", "ę", "Ę"}

    for line in block.lines:
        if not line.spans:
            continue

        fixed_spans = []
        i = 0
        n = len(line.spans)

        while i < n:
            current_span = line.spans[i]
            text = current_span.text

            if not text:
                fixed_spans.append(current_span)
                i += 1
                continue

            fixed_text_chars = []
            j = 0
            length = len(text)
            has_changes = False

            while j < length:
                c_code = ord(text[j])
                if c_code in MAPS and j + 1 < length:
                    next_c_code = ord(text[j + 1])
                    if next_c_code in MAPS[c_code]:
                        fixed_text_chars.append(chr(MAPS[c_code][next_c_code]))
                        j += 2
                        has_changes = True
                        continue
                fixed_text_chars.append(text[j])
                j += 1

            if has_changes:
                text = "".join(fixed_text_chars)
                current_span.text = text

            if text and text[0] in MERGE_TARGETS and fixed_spans:
                prev_span = fixed_spans[-1]
                prev_span.text = prev_span.text + text

                p_box = prev_span.bbox
                c_box = current_span.bbox
                prev_span.bbox = (
                    p_box[0],
                    min(p_box[1], c_box[1]),
                    max(p_box[2], c_box[2]),
                    max(p_box[3], c_box[3]),
                )
            else:
                fixed_spans.append(current_span)

            i += 1

        line.spans = fixed_spans

    return block
