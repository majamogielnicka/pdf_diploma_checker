import fitz  # PyMuPDF
import re

from analysis.extraction.raw_extraction.bare_struct import (
    PageData,
    TocData,
    TocEntry,
    TofData,
    TofEntry,
    TotData,
    TotEntry,
)
def extract_TOC(doc: fitz.Document, pages: list[PageData]) -> TocData | None:
    """Funkcja wykrywająca spis treści"""
    keywords = ["spis treści", "spis tresci", "table of contents", "contents", "toc"]
    all_entries = []
    toc_pages = []
    base_x = None

    is_detecting = True

    for page_obj in pages[:15]:
        if not is_detecting:
            break

        y_groups = {}
        for block in page_obj.text_blocks:
            for line in block.lines:
                y_center = round(line.bbox[1] / 5) * 5
                if y_center not in y_groups:
                    y_groups[y_center] = []
                y_groups[y_center].append(line)

        page_entries = []
        page_text = ""

        for y in sorted(y_groups.keys()):
            lines_on_y = sorted(y_groups[y], key=lambda line: line.bbox[0])

            fragments = []
            for line in lines_on_y:
                for span in line.spans:
                    txt = span.text.strip()
                    if txt:
                        fragments.append(txt)

            if not fragments:
                continue

            line_full_text = " ".join(fragments)
            page_text += line_full_text + " "

            match = re.search(r"^(.*?)(?:\.|\s)*\s+(\d+)$", line_full_text)

            if match:
                title_raw, p_num = match.groups()
                title_clean = re.sub(r"[\.\s·-]{2,}", " ", title_raw).strip()

                if len(title_clean) < 3:
                    continue

                current_x = lines_on_y[0].bbox[0]
                if base_x is None:
                    base_x = current_x

                gap_level = 1 + int(max(0, current_x - base_x) / 12)

                num_match = re.match(r"^(\d+(?:\.\d+)*)\.?", title_clean)
                dotted_level = num_match.group(1).count(".") + 1 if num_match else 1

                is_bold = any(
                    "bold" in span.font.lower()
                    for line in lines_on_y
                    for span in line.spans
                )

                if is_bold and gap_level == 1:
                    final_level = 1
                else:
                    final_level = max(gap_level, dotted_level)

                page_entries.append(
                    TocEntry(
                        level=final_level,
                        title=title_clean,
                        page=int(p_num),
                        bbox=lines_on_y[0].bbox,
                        src_page=page_obj.number,
                    )
                )

        low_page_text = page_text.lower()
        has_keyword = any(word in low_page_text for word in keywords)

        if (has_keyword and len(page_entries) >= 2) or len(page_entries) >= 5:
            all_entries.extend(page_entries)
            if page_obj.number not in toc_pages:
                toc_pages.append(page_obj.number)
        elif len(toc_pages) > 0:
            is_detecting = False

    if all_entries:
        return TocData(
            page_nums=toc_pages, entries=all_entries, text="Wykryto wizualnie "
        )

    built_in_toc = doc.get_toc()
    if built_in_toc:
        entries = [
            TocEntry(
                level=level,
                title=title.strip(),
                page=page,
                bbox=(0, 0, 0, 0),
                src_page=-1,
            )
            for level, title, page in built_in_toc
        ]
        return TocData(page_nums=[-1], entries=entries, text="Wykryto z metadanych")

    return None


def extract_TOF(
    pages: list[PageData], toc_pages: list[int]
) -> TofData | None:  # Table of Figures
    """Funkcja wykrywająca spisy rysunków"""
    keywords = [
        "spis rysunków",
        "spis rysunkow",
        "spis ilustracji",
        "list of figures",
        "table of figures",
        "wykaz rysunkow",
        "wykaz rysunków",
        "spis wykresów",
        "table of graphs",
    ]
    anti_keywords = [
        "spis tabel",
        "spis tablic",
        "list of tables",
        "wykaz tabel",
        "bibliografia",
        "bibliography",
    ]
    all_entries = []
    tof_pages = []
    is_detecting = False

    for page_obj in pages:
        if page_obj.number in toc_pages:
            continue
        page_text = ""
        y_groups = {}

        for block in page_obj.text_blocks:
            for line in block.lines:
                y_center = round(line.bbox[1] / 5) * 5
                if y_center not in y_groups:
                    y_groups[y_center] = []
                y_groups[y_center].append(line)

        has_keyword_on_top = False
        has_anti_keyword_on_top = False
        top_lines_text = ""

        for y in sorted(y_groups.keys()):
            first_line_in_group = y_groups[y][0]
            if first_line_in_group.bbox[1] < (page_obj.height * 0.15):
                lines_on_y = sorted(y_groups[y], key=lambda line: line.bbox[0])
                for line in lines_on_y:
                    top_lines_text += (
                        " ".join(
                            [
                                span.text.strip()
                                for span in line.spans
                                if span.text.strip()
                            ]
                        )
                        + " "
                    )
            else:
                break

        top_text_low = top_lines_text.lower()
        if any(word in top_text_low for word in keywords):
            has_keyword_on_top = True
        if any(word in top_text_low for word in anti_keywords):
            has_anti_keyword_on_top = True

        if has_keyword_on_top:
            is_detecting = True
        elif is_detecting:
            if has_anti_keyword_on_top or (
                tof_pages and page_obj.number != (tof_pages[-1] + 1)
            ):
                is_detecting = False

        page_entries = []
        cut_obj_num = ""
        cut_title = ""
        for y in sorted(y_groups.keys()):
            lines_on_y = sorted(y_groups[y], key=lambda line: line.bbox[0])
            fragments = []
            for line in lines_on_y:
                for span in line.spans:
                    txt = span.text.strip()
                    if txt:
                        fragments.append(txt)
            if not fragments:
                continue

            line_full_text = " ".join(fragments)
            if line_full_text.lower() in keywords:
                page_text += line_full_text + " "
                continue

            page_text += line_full_text + " "
            match_full = re.search(
                r"^(?:[A-Z][a-zśł]{3,10}\.?\s*)?([A-Z\d]+(?:\.[A-Z\d]+)*)\.?\s+(.*?)(?:\.|\s)*\s+(\d+)$",
                line_full_text,
            )
            match_start = re.match(
                r"^(?:[A-Z][a-zśł]{3,10}\.?\s*)?([A-Z\d]+(?:\.[A-Z\d]+)*)\.?\s+(.*)",
                line_full_text,
            )
            match_end = re.search(r"(.*?)(?:\.|\s)*\s+(\d+)$", line_full_text)

            if match_full:
                obj_num, title_raw, p_num = match_full.groups()
                sep = "" if cut_title.endswith("-") else " "
                base_title = cut_title[:-1] if cut_title.endswith("-") else cut_title
                full_title = (base_title + sep + title_raw).strip()
                title_clean = re.sub(r"[\.\s·-]{2,}", " ", full_title).strip()
                page_entries.append(
                    TofEntry(
                        number=obj_num,
                        title=title_clean,
                        page=int(p_num),
                        bbox=lines_on_y[0].bbox,
                        src_page=page_obj.number,
                    )
                )
                cut_obj_num = ""
                cut_title = ""
            elif match_start:
                cut_obj_num = match_start.group(1)
                cut_title = match_start.group(2)
            elif match_end and cut_obj_num:
                title_part, p_num = match_end.groups()
                sep = "" if cut_title.endswith("-") else " "
                base_title = cut_title[:-1] if cut_title.endswith("-") else cut_title
                full_title = (base_title + sep + title_part).strip()
                title_clean = re.sub(r"[\.\s·-]{2,}", " ", full_title).strip()
                page_entries.append(
                    TofEntry(
                        number=cut_obj_num,
                        title=title_clean,
                        page=int(p_num),
                        bbox=lines_on_y[0].bbox,
                        src_page=page_obj.number,
                    )
                )
                cut_obj_num = ""
                cut_title = ""
            elif cut_obj_num:
                sep = "" if cut_title.endswith("-") else " "
                base_title = cut_title[:-1] if cut_title.endswith("-") else cut_title
                cut_title = base_title + sep + line_full_text

        if is_detecting and page_entries:
            if len(tof_pages) == 0 and len(page_entries) < 2:
                is_detecting = False
            else:
                all_entries.extend(page_entries)
                if page_obj.number not in tof_pages:
                    tof_pages.append(page_obj.number)
        elif is_detecting and not page_entries:
            is_detecting = False

    if all_entries:
        return TofData(page_nums=tof_pages, entries=all_entries, text="Spis Rysunków")
    return None


def extract_TOT(
    pages: list[PageData], toc_pages: list[int]
) -> TotData | None:  # Table of Tables
    """Funkcja wykrywająca spisy tabel"""
    keywords = ["spis tabel", "spis tablic", "list of tables", "wykaz tabel"]
    anti_keywords = [
        "spis rysunków",
        "spis rysunkow",
        "spis ilustracji",
        "list of figures",
        "table of figures",
        "wykaz rysunkow",
        "wykaz rysunków",
        "spis wykresów",
        "table of graphs",
        "bibliografia",
        "bibliography",
    ]
    all_entries = []
    tot_pages = []
    is_detecting = False

    for page_obj in pages:
        if page_obj.number in toc_pages:
            continue
        page_text = ""
        y_groups = {}

        for block in page_obj.text_blocks:
            for line in block.lines:
                y_center = round(line.bbox[1] / 5) * 5
                if y_center not in y_groups:
                    y_groups[y_center] = []
                y_groups[y_center].append(line)

        has_keyword_on_top = False
        has_anti_keyword_on_top = False
        top_lines_text = ""

        for y in sorted(y_groups.keys()):
            first_line_in_group = y_groups[y][0]
            if first_line_in_group.bbox[1] < (page_obj.height * 0.15):
                lines_on_y = sorted(y_groups[y], key=lambda line: line.bbox[0])
                for line in lines_on_y:
                    top_lines_text += (
                        " ".join(
                            [
                                span.text.strip()
                                for span in line.spans
                                if span.text.strip()
                            ]
                        )
                        + " "
                    )
            else:
                break

        top_text_low = top_lines_text.lower()
        if any(word in top_text_low for word in keywords):
            has_keyword_on_top = True
        if any(word in top_text_low for word in anti_keywords):
            has_anti_keyword_on_top = True

        if has_keyword_on_top:
            is_detecting = True
        elif is_detecting:
            if has_anti_keyword_on_top or (
                tot_pages and page_obj.number != (tot_pages[-1] + 1)
            ):
                is_detecting = False

        page_entries = []
        cut_obj_num = ""
        cut_title = ""
        for y in sorted(y_groups.keys()):
            lines_on_y = sorted(y_groups[y], key=lambda line: line.bbox[0])
            fragments = []
            for line in lines_on_y:
                for span in line.spans:
                    txt = span.text.strip()
                    if txt:
                        fragments.append(txt)
            if not fragments:
                continue

            line_full_text = " ".join(fragments)
            if line_full_text.lower() in keywords:
                page_text += line_full_text + " "
                continue

            page_text += line_full_text + " "
            match_full = re.search(
                r"^(?:[A-Z][a-zśł]{3,10}\.?\s*)?([A-Z\d]+(?:\.[A-Z\d]+)*)\.?\s+(.*?)(?:\.|\s)*\s+(\d+)$",
                line_full_text,
            )
            match_start = re.match(
                r"^(?:[A-Z][a-zśł]{3,10}\.?\s*)?([A-Z\d]+(?:\.[A-Z\d]+)*)\.?\s+(.*)",
                line_full_text,
            )
            match_end = re.search(r"(.*?)(?:\.|\s)*\s+(\d+)$", line_full_text)

            if match_full:
                obj_num, title_raw, p_num = match_full.groups()
                sep = "" if cut_title.endswith("-") else " "
                base_title = cut_title[:-1] if cut_title.endswith("-") else cut_title
                full_title = (base_title + sep + title_raw).strip()
                title_clean = re.sub(r"[\.\s·-]{2,}", " ", full_title).strip()
                page_entries.append(
                    TotEntry(
                        number=obj_num,
                        title=title_clean,
                        page=int(p_num),
                        bbox=lines_on_y[0].bbox,
                        src_page=page_obj.number,
                    )
                )
                cut_obj_num = ""
                cut_title = ""
            elif match_start:
                cut_obj_num = match_start.group(1)
                cut_title = match_start.group(2)
            elif match_end and cut_obj_num:
                title_part, p_num = match_end.groups()
                sep = "" if cut_title.endswith("-") else " "
                base_title = cut_title[:-1] if cut_title.endswith("-") else cut_title
                full_title = (base_title + sep + title_part).strip()
                title_clean = re.sub(r"[\.\s·-]{2,}", " ", full_title).strip()
                page_entries.append(
                    TotEntry(
                        number=cut_obj_num,
                        title=title_clean,
                        page=int(p_num),
                        bbox=lines_on_y[0].bbox,
                        src_page=page_obj.number,
                    )
                )
                cut_obj_num = ""
                cut_title = ""
            elif cut_obj_num:
                sep = "" if cut_title.endswith("-") else " "
                base_title = cut_title[:-1] if cut_title.endswith("-") else cut_title
                cut_title = base_title + sep + line_full_text

        if is_detecting and page_entries:
            if len(tot_pages) == 0 and len(page_entries) < 2:
                is_detecting = False
            else:
                all_entries.extend(page_entries)
                if page_obj.number not in tot_pages:
                    tot_pages.append(page_obj.number)
        elif is_detecting and not page_entries:
            is_detecting = False

    if all_entries:
        return TotData(page_nums=tot_pages, entries=all_entries, text="Spis Tabel")
    return None
