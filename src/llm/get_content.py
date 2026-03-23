import re
import fitz
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import fitz

file_path = Path("src/theses/doju1.pdf")
output_path = Path("src/llm/wyniki/blocks.txt")
summaries_path = Path("src/llm/wyniki/subtitles.txt")


def get_font_size(pdf_path):
    doc = fitz.open(pdf_path)
    sizes = []

    for page in doc:
        page_dict = page.get_text("dict", sort=True)

        for block in page_dict["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text and not text.isdigit():
                        sizes.append(round(float(span["size"]), 1))

    doc.close()

    if not sizes:
        return 11.0

    counts = Counter(sizes)
    body_size = counts.most_common(1)[0][0]
    larger_sizes = sorted(size for size in counts if size > body_size)

    if larger_sizes:
        return larger_sizes[0]

    return body_size


@dataclass
class ChapterBlock:
    id: int
    title: str
    content: str = ""


@dataclass
class SubtitleBlock:
    id: int
    number: str
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
    font_size = get_font_size(path)

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


def split_subtitles(path):
    doc = fitz.open(path)
    subtitle_blocks = []

    current_number = ""
    current_title = ""
    current_text_parts = []
    block_id = 1

    subtitle_pattern = re.compile(r"^(\d+(?:\.\d+)+)\.?\s+(.*)$")

    for page in doc:
        page_dict = page.get_text("dict", sort=True)

        for b in page_dict["blocks"]:
            if "lines" not in b:
                continue

            for line in b["lines"]:
                line_text = " ".join(
                    span["text"].strip()
                    for span in line["spans"]
                    if span["text"].strip()
                ).strip()

                if not line_text:
                    continue

                match = subtitle_pattern.match(line_text)

                if match:
                    if current_number and current_text_parts:
                        subtitle_blocks.append(
                            SubtitleBlock(
                                id=block_id,
                                number=current_number,
                                title=current_title,
                                content=" ".join(current_text_parts).strip()
                            )
                        )
                        block_id += 1

                    current_number = match.group(1)
                    current_title = match.group(2).strip()
                    current_text_parts = []
                else:
                    if current_number:
                        current_text_parts.append(line_text)

    if current_number and current_text_parts:
        subtitle_blocks.append(
            SubtitleBlock(
                id=block_id,
                number=current_number,
                title=current_title,
                content=" ".join(current_text_parts).strip()
            )
        )

    doc.close()
    return subtitle_blocks


def export_blocks(blocks, output_path):
    formatted_parts = []

    for block in blocks:
        formatted_parts.append(
            f"{block.id}. {block.title}\n{block.content}\n"
        )

    result = "\n".join(formatted_parts).strip()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"Zapisano do: {output_path}")


def export_subtitles(subtitle_blocks, output_path):
    formatted_parts = []

    for block in subtitle_blocks:
        formatted_parts.append(
            f"{block.id}. {block.number} {block.title}\n{block.content}\n"
        )

    result = "\n".join(formatted_parts).strip()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"Zapisano do: {output_path}")


if __name__ == "__main__":
    subtitle_blocks = split_subtitles(file_path)
    export_subtitles(subtitle_blocks, summaries_path)