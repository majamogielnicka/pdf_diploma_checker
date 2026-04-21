import re
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)



from src.analysis.extraction.helper_llm.extraction_json_llm import extractPDF
from src.analysis.extraction.helper_llm.converter_linguistics_llm import PDFMapper

file_path = PROJECT_ROOT / "data" / "kana.pdf"

NUMBERED_HEADING_RE = re.compile(r"^\s*(\d+\.\d+(?:\.\d+)*)(?:\.)?\s+(.+?)\s*$")
HEADING_WITH_PREFIX_RE = re.compile(r"^\s*(?:\d+\.\s+)?(\d+\.\d+(?:\.\d+)*)(?:\.)?\s+(.+?)\s*$")

DOT_LEADER_RE = re.compile(r"\.\s*\.\s*\.\s*\.")
MULTISPACE_RE = re.compile(r"\s+")


def clean_ws(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")
    return MULTISPACE_RE.sub(" ", text).strip()


def parse_heading(text: str):
    text = clean_ws(text)
    m = HEADING_WITH_PREFIX_RE.match(text)
    if not m:
        return None
    number = m.group(1)
    title = m.group(2).strip()
    return number, title


def is_numbered_heading(text: str) -> bool:
    return parse_heading(text) is not None


def looks_like_toc_entry(text: str) -> bool:
    return bool(DOT_LEADER_RE.search(clean_ws(text)))


def is_probable_toc_heading(text: str) -> bool:
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
    parsed = parse_heading(text)
    if not parsed:
        return clean_ws(text).lower()
    number, title = parsed
    return f"{number} {clean_ws(title).lower()}"


def get_level(number: str) -> int:
    return number.count(".") + 1


def load_logical_blocks_from_pdf(pdf_path: Path):
    raw_doc = extractPDF(str(pdf_path))
    mapped_doc = PDFMapper.map_to_schema(raw_doc)
    return mapped_doc.logical_blocks


def get_block_type(block):
    return getattr(block, "type", None)


def is_text_block(block) -> bool:
    return get_block_type(block) in (None, "paragraph")


def get_block_content(block) -> str:
    return clean_ws(getattr(block, "content", "") or "")


def is_real_heading_candidate(block) -> bool:
    text = get_block_content(block)
    if not text:
        return False
    if is_probable_toc_heading(text):
        return False
    return is_numbered_heading(text)


def next_heading_index(logical_blocks, start_idx: int, current_level: int) -> int:
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


def extract_subtitles_from_pdf(pdf_path: Path):
    logical_blocks = load_logical_blocks_from_pdf(pdf_path)
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
    for sub in subtitles:
        print(sub["display"])
        preview = sub["content"][:max_chars].strip()
        if len(sub["content"]) > max_chars:
            preview += "..."
        print(preview)
        print("-" * 80)


def get_subtitles(pdf_path: Path, txt_path: Path | None = None):
    subtitles = extract_subtitles_from_pdf(pdf_path)

    if txt_path is not None:
        export_subtitles_to_txt(subtitles, txt_path)

    return subtitles


def main():
    pdf_path = Path(file_path)
    txt_path = Path("src/llm/wyniki/subtitles.txt")

    subtitles = get_subtitles(pdf_path, txt_path)
    print_subtitles(subtitles)


if __name__ == "__main__":
    main()