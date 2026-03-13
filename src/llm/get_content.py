import fitz
from dataclasses import dataclass
from pathlib import Path

file_path = Path("src/theses/ch.pdf")

@dataclass
class ChapterBlock:
    id: int
    title: str
    content: str = ""


def get_text(path):
    doc = fitz.open(path)
    text_parts = []

    for page in doc:
        page_text = page.get_text("text")
        if page_text:
            text_parts.append(page_text.strip())

    doc.close()
    return "\n".join(text_parts).strip()


def get_content(path):
    doc = fitz.open(path)
    blocks = []

    current_title = ""
    current_text_parts = []
    block_id = 1
    font_size = 11

    for page in doc:
        page_dict = page.get_text("dict", sort=True)

        for b in page_dict["blocks"]:
            if "lines" not in b:
                continue

            for line in b["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text or text.isdigit():
                        continue

                    size = span["size"]
                    is_bold = bool(span["flags"] & 16)
                    is_header = (size >= font_size and is_bold) and len(text) > 3 and text.isupper()

                    if is_header:
                        if not current_text_parts and current_title:
                            current_title = f"{current_title} {text}"
                        else:
                            if current_text_parts:
                                full_content = " ".join(current_text_parts).strip()
                                if len(full_content) > 5:
                                    blocks.append(
                                        ChapterBlock(
                                            id=block_id,
                                            title=current_title,
                                            content=full_content
                                        )
                                    )
                                    block_id += 1

                            current_title = text
                            current_text_parts = []
                    else:
                        if current_title:
                            current_text_parts.append(text)

    if current_title and current_text_parts:
        blocks.append(
            ChapterBlock(
                id=block_id,
                title=current_title,
                content=" ".join(current_text_parts).strip()
            )
        )

    doc.close()
    return blocks

if __name__=="__main__":
    print(get_text(file_path))