"""Extract numbered subtitle sections and their content from mapped PDF blocks."""

import re
import os
from pathlib import Path
import sys

_src_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for _p in (os.path.dirname(_src_dir), _src_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common.path import resource_path

from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
from analysis.extraction.helper_llm.converter_linguistics_llm import PDFMapper_llm
from analysis.modules.llm.config import THESIS_PATH

file_path = THESIS_PATH

NUMBERED_HEADING_RE = re.compile(r"^\s*(\d+\.\d+(?:\.\d+)*)(?:\.)?\s+(.+?)\s*$")
HEADING_WITH_PREFIX_RE = re.compile(r"^\s*(?:\d+\.\s+)?(\d+\.\d+(?:\.\d+)*)(?:\.)?\s+(.+?)\s*$")

DOT_LEADER_RE = re.compile(r"\.\s*\.\s*\.\s*\.")
MULTISPACE_RE = re.compile(r"\s+")


def clean_ws(text: str) -> str:
    """Normalize whitespace and remove soft hyphens/non-breaking spaces."""

    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")
    return MULTISPACE_RE.sub(" ", text).strip()


def parse_heading(text: str):
    """Parse a numbered heading and return a (number, title) tuple."""

    text = clean_ws(text)
    m = HEADING_WITH_PREFIX_RE.match(text)
    if not m:
        return None
    number = m.group(1)
    title = m.group(2).strip()
    return number, title


def is_numbered_heading(text: str) -> bool:
    """Return True when text matches the expected numbered heading pattern."""

    return parse_heading(text) is not None


def looks_like_toc_entry(text: str) -> bool:
    """Return True when text looks like a table-of-contents line."""

    return bool(DOT_LEADER_RE.search(clean_ws(text)))


def is_probable_toc_heading(text: str) -> bool:
    """Heuristically detect headings that likely belong to TOC or indexes."""

    text = clean_ws(text)

    if not text:
        return False

    if looks_like_toc_entry(text):
        return True

    if re.search(r"\b(rozdział|chapter|spis tabel|spis wykresów|bibliografia|zakończenie|wstęp|spis rycin)\b", text.lower()):
        return True

    if re.search(r"\b(procent|odpowiedź|źródło|tabela|rycina)\b", text.lower()):
        return True

    if re.match(r"^\d+\s*$", text):
        return True

    if re.match(r"^\d+\s+[A-ZĄĆĘŁŃÓŚŹŻa-ząćęłńóśźż].*", text) and not re.match(r"^\d+\.\d+(?:\.\d+)*", text):
        return True

    if re.match(r"^\d+\s+[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż].*\d", text):
        return True

    return False


def heading_key(text: str) -> str:
    """Build a normalized key for deduplicating detected headings."""

    parsed = parse_heading(text)
    if not parsed:
        return clean_ws(text).lower()
    number, title = parsed
    return f"{number} {clean_ws(title).lower()}"


def get_level(number: str) -> int:
    """Return heading depth level derived from dotted numbering."""

    return number.count(".") + 1


def load_logical_blocks_from_pdf(raw_doc):
    """Map raw extraction output to logical blocks."""

    mapped_doc = PDFMapper_llm.map_to_schema(raw_doc)
    return mapped_doc.logical_blocks


def get_block_type(block):
    """Return block type attribute when available."""

    return getattr(block, "type", None)


def is_text_block(block) -> bool:
    """Return True when a block should be treated as paragraph text."""

    return get_block_type(block) in (None, "paragraph")


def get_block_content(block) -> str:
    """Return normalized text content of a logical block."""

    return clean_ws(getattr(block, "content", "") or "")


def is_real_heading_candidate(block) -> bool:
    """Filter out non-heading and TOC-like candidates."""

    text = get_block_content(block)
    if not text:
        return False
    if is_probable_toc_heading(text):
        return False
    return is_numbered_heading(text)


def next_heading_index(logical_blocks, start_idx: int, current_level: int) -> int:
    """Find the index of the next heading at same or higher hierarchy level."""

    for i in range(start_idx + 1, len(logical_blocks)):
        text = get_block_content(logical_blocks[i])
        if not text:
            continue

        parsed = parse_heading(text)
        if not parsed:
            continue

        if is_probable_toc_heading(text):
            continue

        next_number, _ = parsed
        next_level = get_level(next_number)

        if next_level <= current_level:
            return i

    return len(logical_blocks)


def collect_section_text(logical_blocks, start_idx: int, end_idx: int) -> str:
    """Collect section body text between two heading indices."""

    parts = []

    for block in logical_blocks[start_idx + 1:end_idx]:
        block_type = get_block_type(block)
        if block_type not in (None, "paragraph"):
            continue

        text = get_block_content(block)
        if not text:
            continue
        if looks_like_toc_entry(text):
            continue
        if is_probable_toc_heading(text):
            continue
        if is_numbered_heading(text):
            continue

        parts.append(text)

    return "\n".join(parts).strip()


def find_real_numbered_headings(logical_blocks):
    """Return deduplicated numbered headings sorted by source order."""

    candidates = []

    for idx, block in enumerate(logical_blocks):
        if not is_real_heading_candidate(block):
            continue

        text = get_block_content(block)
        parsed = parse_heading(text)
        if not parsed:
            continue

        number, title = parsed

        candidates.append({
            "index": idx,
            "number": number,
            "title": title,
            "display": f"{number} {title}",
            "key": heading_key(text),
            "level": get_level(number),
        })

    latest_by_key = {}
    for h in candidates:
        latest_by_key[h["key"]] = h

    return sorted(latest_by_key.values(), key=lambda x: x["index"])


def extract_subtitles_from_pdf(raw_doc):
    """Extract subtitles with section content from raw PDF extraction output."""

    logical_blocks = load_logical_blocks_from_pdf(raw_doc)
    headings = find_real_numbered_headings(logical_blocks)

    subtitles = []
    for h in headings:
        end_idx = next_heading_index(logical_blocks, h["index"], h["level"])
        body = collect_section_text(logical_blocks, h["index"], end_idx)

        subtitles.append({
            "number": h["number"],
            "title": h["title"],
            "display": h["display"],
            "level": h["level"],
            "content": body,
        })

    return subtitles


def export_subtitles_to_txt(subtitles, txt_path: Path):
    """Export extracted subtitles and one-line content previews to a text file."""

    txt_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for sub in subtitles:
        one_line_content = re.sub(r"\s+", " ", sub["content"]).strip()
        lines.append(sub["display"])
        if one_line_content:
            lines.append(one_line_content)
        lines.append("")

    txt_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def print_subtitles(subtitles, max_chars: int = 250):
    """Print subtitle titles with truncated content previews."""

    for sub in subtitles:
        print(sub["display"])
        preview = sub["content"][:max_chars].strip()
        if len(sub["content"]) > max_chars:
            preview += "..."
        print(preview)
        print("-" * 80)


def get_subtitles(raw_doc, txt_path: Path | None = None):
    """Extract subtitles and optionally save them to a text file."""

    subtitles = extract_subtitles_from_pdf(raw_doc)

    if txt_path is not None:
        export_subtitles_to_txt(subtitles, txt_path)

    return subtitles


def main():
    """Run subtitle extraction for the configured thesis file and print results."""

    pdf_path = Path(file_path)
    txt_path = Path(resource_path(os.path.join("llm", "wyniki", "subtitles.txt")))

    raw_doc = extractPDF_llm(str(pdf_path))

    subtitles = get_subtitles(raw_doc)
    print_subtitles(subtitles)


if __name__ == "__main__":
    main()