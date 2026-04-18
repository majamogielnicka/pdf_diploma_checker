import os
from pathlib import Path
import sys 

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]

sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.extraction.extraction_json import extractPDF
from src.analysis.extraction.bare_struct import PageData, TocEntry

path = PROJECT_ROOT / "data" / "doju1.pdf"

def extract_sections_content(pages: list[PageData], toc_entries: list[TocEntry]) -> list[dict]:
    """
    Funkcja, mająca na celu wyekstraktowanie konkretnych rozdziałów wraz z ich zawwartościami dla LLM
    """
    sections = []
    sorted_toc = sorted(toc_entries, key=lambda x: (x.page, x.bbox[1]))

    for i, entry in enumerate(sorted_toc):
        cur_title = entry.title
        start_page_idx = entry.page - 1 
        
        next_entry = sorted_toc[i + 1] if i + 1 < len(sorted_toc) else None
        content = []
        found_next = False

        for p_idx in range(start_page_idx, len(pages)):
            if found_next:
                break
                
            page = pages[p_idx]
            for block in page.text_blocks:
                if getattr(block, 'block_type', '') == 'footer':
                    continue

                block_text = " ".join([" ".join([s.text for s in l.spans]) for l in block.lines])
                block_text = " ".join(block_text.split()).strip()

                if not block_text:
                    continue

                if next_entry and p_idx >= (next_entry.page - 1):
                    if next_entry.title.lower() in block_text.lower():
                        found_next = True
                        break

                if p_idx == start_page_idx and cur_title.lower() in block_text.lower():
                    continue

                content.append(block_text)

        sections.append({
            "section_title": cur_title,
            "section_text": "\n".join(content)
        })

    return sections

def main(path: str):
    document_data = extractPDF(path)
    if not document_data or not document_data.toc or not document_data.toc.entries:
        print("Nie znaleziono spisu treści")
        return

    sections = extract_sections_content(document_data.pages, document_data.toc.entries)
    for section in sections:
        print(f"{section['section_title']}")
        text= section['section_text'][:100].replace('\n', ' ')
        print(f"{text}...")
        print("-" * 30)

if __name__ == "__main__":
    main(path)