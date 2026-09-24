
import fitz  # PyMuPDF

from analysis.extraction.raw_extraction.bare_struct import (
    PageData,
    TableInfo,
)

from analysis.extraction.raw_extraction.text_extractor import (
    fix_latex,
)

def find_table_description(table_bbox, text_blocks, priority_side=None):
    """
    Locates the caption or description for a table by analyzing the spatial relationship
    of surrounding text blocks relative to the table's bounding box. Groups potential
    matches by their position (above or below) and specific keywords.

    Args:
        table_bbox (list): The bounding box of the table [x0, y0, x1, y1].
        text_blocks (list): A list of text blocks to evaluate as potential captions.
        priority_side (str, optional): The preferred side to check first ('above' or 'below').
            Defaults to None.

    Returns:
        tuple[str, str]: A tuple containing the extracted description text and the
        side it was found on ('above' or 'below').
    """
    x0, y0, x1, y1 = table_bbox
    # Rozdzielamy potencjalne opisy na górę i dół oraz sprawdzamy słowa kluczowe
    kw_matches = {"above": [], "below": []}
    other_matches = {"above": [], "below": []}

    for block in text_blocks:
        bx0, by0, bx1, by1 = block.bbox

        # 1. Szukanie odległości pionowej
        is_close_above = abs(by1 - y0) < 40  # Nad tabelą
        is_close_below = abs(by0 - y1) < 60  # Pod tabelą

        if is_close_above or is_close_below:
            full_text = " ".join(
                span.text for line in block.lines for span in line.spans
            ).strip()
            side = "above" if is_close_above else "below"

            # 2. Szukanie czy tekst zaczyna się od "Tabela" lub "Tab."
            if full_text.lower().startswith(
                ("tabele", "tabela", "tab.", "table", "tab")
            ):
                kw_matches[side].append(full_text)
            else:
                other_matches[side].append(full_text)

    # Ustalenie kolejności sprawdzania
    primary = priority_side if priority_side else "above"
    secondary = "below" if primary == "above" else "above"

    # Priorytetyzacja:
    # 1. Słowo kluczowe na preferowanej stronie
    if kw_matches[primary]:
        return kw_matches[primary][0], primary
    # 2. Słowo kluczowe na jakiejkolwiek stronie
    if kw_matches[secondary]:
        return kw_matches[secondary][0], secondary
    # 3. Zwykły tekst na preferowanej stronie
    if other_matches[primary]:
        return other_matches[primary][0], primary
    # 4. Zwykły tekst na jakiejkolwiek stronie
    if other_matches[secondary]:
        return other_matches[secondary][0], secondary

    return "", priority_side



def extract_tables(
    page: fitz.Page, drawings: list, cur_page: PageData, priority_side=None
) -> tuple[list, str]:
    """
    Extracts tables from a given PDF page and passes them to json.

    Args:
        page (fitz.Page): The PDF page
        drawings (list): A list of vector drawings on the page, used to ignore flowcharts.
        cur_page (PageData): The data object for the current page where extracted tables are appended.
        priority_side (str, optional): The preferred side (above/below) to look for descriptions.

    Returns:
        tuple: A tuple containing a list of fitz.Rect objects representing the bounding boxes of the extracted tables, and a string indicating the priority side.
    """
    table_bboxes = []
    # TODO: znajdywanie tabel typu APA czyli, takich z niestandardowym obramowaniem bez linii poziomych albo jakichkolwiek linii. ogólna poprawa działania funkcji
    # znajdowanie tabel, wyciąganie danych i zapisywanie do list
    tabs = page.find_tables(strategy="lines_strict")
    for tab in tabs.tables:
        extracted_data = tab.extract()

        if tab.col_count < 2:
            continue

        if tab.row_count <= 3:
            expanded_bbox = fitz.Rect(tab.bbox) + (-40, -40, 40, 40)
        else:
            expanded_bbox = fitz.Rect(tab.bbox) + (-2, -2, 2, 2)

        curve_count = 0
        diag_count = 0

        for d in drawings:
            d_rect = fitz.Rect(d["rect"])

            if d_rect.intersects(expanded_bbox):
                for item in d["items"]:
                    if item[0] == "l":
                        p1, p2 = item[1], item[2]
                        if abs(p1.x - p2.x) > 3 and abs(p1.y - p2.y) > 3:
                            diag_count += 1
                    elif item[0] in ("c", "q"):
                        if d_rect.width > 5 and d_rect.height > 5:
                            curve_count += 1

        if curve_count > 0 or diag_count > 1:
            continue

        # usuwa entery i zamienia na spacje, można potem usunąć jakbyśmy chcieli widzieć gdzie są entery
        cleaned_data = [
            [cell.replace("\n", " ").strip() if cell else "" for cell in row]
            for row in extracted_data
        ]

        # zabezpieczenie przed zapisywaniem wykresów jako tabelek
        total_cells = tab.row_count * tab.col_count
        if total_cells > 0:
            filled_cells = sum(1 for row in cleaned_data for cell in row if cell != "")
            fill_ratio = filled_cells / total_cells

            if fill_ratio < 0.20:
                continue

        total_chars = sum(len(cell) for row in cleaned_data for cell in row)
        avg_chars_per_cell = total_chars / filled_cells if filled_cells > 0 else 0
        if fill_ratio < 0.50 and avg_chars_per_cell < 8:
            continue

        description, found_side = find_table_description(
            tab.bbox, cur_page.text_blocks, priority_side
        )
        if description and priority_side is None:
            priority_side = found_side

        table_bboxes.append(fitz.Rect(tab.bbox))
        cur_page.tables.append(
            TableInfo(
                bbox=tab.bbox,
                row_count=tab.row_count,
                col_count=tab.col_count,
                description=description,
                data=cleaned_data,
            )
        )

    return table_bboxes, priority_side


def extract_apa_tables(
    page: fitz.Page,
    drawings: list,
    cur_page: PageData,
    existing_table_bboxes: list,
    priority_side=None,
) -> tuple[list, str]:
    """
    Extracts APA-style tables (characterized by horizontal lines and absence of vertical lines) from a given PDF page and passes them to json.

    Args:
        page (fitz.Page): The PDF page.
        drawings (list): A list of vector drawings on the page, used to identify horizontal lines forming the table structure.
        cur_page (PageData): The data object for the current page where extracted tables are appended.
        existing_table_bboxes (list): A list of bounding boxes from already extracted tables to avoid duplication.
        priority_side (str, optional): The preferred side (above/below) to look for descriptions.

    Returns:
        tuple: A tuple containing a list of fitz.Rect objects representing the bounding boxes of the extracted APA tables, and a string indicating the priority side.
    """
    apa_bboxes = []

    horizontal_lines = []
    for d in drawings:
        rect = fitz.Rect(d["rect"])
        if rect.height <= 4 and rect.width > 100:
            horizontal_lines.append(rect)

    horizontal_lines = sorted(horizontal_lines, key=lambda r: r.y0)

    grouped_table_rects = []
    used_lines = set()

    for i, line in enumerate(horizontal_lines):
        if i in used_lines:
            continue
        current_group = [line]
        used_lines.add(i)

        for j, other_line in enumerate(horizontal_lines[i + 1 :], start=i + 1):
            if j in used_lines:
                continue
            if abs(line.x0 - other_line.x0) < 25 and abs(line.x1 - other_line.x1) < 25:
                if other_line.y0 - current_group[-1].y0 < 500:
                    current_group.append(other_line)
                    used_lines.add(j)

        if len(current_group) >= 2:
            top_y = current_group[0].y0 - 10
            bottom_y = current_group[-1].y1 + 10
            min_x = min(line.x0 for line in current_group) - 10
            max_x = max(line.x1 for line in current_group) + 10
            apa_rect = fitz.Rect(min_x, top_y, max_x, bottom_y)
            grouped_table_rects.append(apa_rect)

    for apa_rect in grouped_table_rects:
        is_duplicate = False
        for existing_rect in existing_table_bboxes:
            intersect = apa_rect & existing_rect
            if intersect.is_valid and not intersect.is_empty:
                overlap_area = intersect.width * intersect.height
                if (
                    overlap_area
                    / min(
                        apa_rect.width * apa_rect.height,
                        existing_rect.width * existing_rect.height + 0.001,
                    )
                    > 0.15
                ):
                    is_duplicate = True
                    break
        if is_duplicate:
            continue

        words = page.get_text("words", clip=apa_rect)
        if not words:
            continue

        words.sort(key=lambda w: w[1])
        top_y = words[0][1]
        header_words = [w for w in words if w[1] < top_y + 15]
        header_words.sort(key=lambda w: w[0])

        col_dividers = [apa_rect.x0 - 10]
        last_x1 = -999
        is_first = True
        for w in header_words:
            if is_first:
                is_first = False
                last_x1 = w[2]
                continue

            if w[0] > last_x1 + 15:
                col_dividers.append(w[0] - 5)
            last_x1 = max(last_x1, w[2])
        col_dividers.append(apa_rect.x1 + 10)

        num_cols = len(col_dividers) - 1
        if num_cols < 2:
            continue

        words.sort(key=lambda w: (w[1], w[0]))
        lines = []
        current_line = []
        last_y = -999
        for w in words:
            if abs(w[1] - last_y) > 4:
                if current_line:
                    current_line.sort(key=lambda x: x[0])
                    lines.append(current_line)
                current_line = [w]
                last_y = w[1]
            else:
                current_line.append(w)
        if current_line:
            current_line.sort(key=lambda x: x[0])
            lines.append(current_line)

        grid = []
        for line in lines:
            row_data = [""] * num_cols
            for w in line:
                c_idx = num_cols - 1
                for c in range(num_cols):
                    if w[0] < col_dividers[c + 1]:
                        c_idx = c
                        break
                row_data[c_idx] += fix_latex(w[4]) + " "
            grid.append([cell.strip() for cell in row_data])

        final_data = []
        for row in grid:
            if not any(row):
                continue
            if not final_data:
                final_data.append(row)
                continue

            if row[0] == "":
                for c in range(num_cols):
                    if row[c]:
                        prev = final_data[-1][c]
                        if prev and prev.endswith("-"):
                            final_data[-1][c] = prev[:-1] + row[c]
                        elif prev:
                            final_data[-1][c] = prev + " " + row[c]
                        else:
                            final_data[-1][c] = row[c]
            else:
                final_data.append(row)

        total_cells = len(final_data) * num_cols if final_data else 0
        if total_cells > 0:
            filled_cells = sum(1 for row in final_data for cell in row if cell != "")
            if (filled_cells / total_cells) < 0.20:
                continue

        description, found_side = find_table_description(
            apa_rect, cur_page.text_blocks, priority_side
        )
        if description and priority_side is None:
            priority_side = found_side

        apa_bboxes.append(apa_rect)
        cur_page.tables.append(
            TableInfo(
                bbox=(apa_rect.x0, apa_rect.y0, apa_rect.x1, apa_rect.y1),
                row_count=len(final_data),
                col_count=num_cols,
                description=description,
                data=final_data,
                table_type="apa",
            )
        )

    return apa_bboxes, priority_side


def extract_lineless_tables(
    page: fitz.Page, cur_page: PageData, existing_table_bboxes: list, priority_side=None
) -> tuple[list, str]:
    """
    Extracts tables completely lacking borders (lineless tables) from a given PDF page and passes them to json.

    Args:
        page (fitz.Page): The PDF page.
        cur_page (PageData): The data object for the current page where extracted tables are appended.
        existing_table_bboxes (list): A list of bounding boxes from already extracted tables to avoid duplication.
        priority_side (str, optional): The preferred side (above/below) to look for descriptions, which also dictates the scanning direction (up/down).

    Returns:
        tuple: A tuple containing a list of fitz.Rect objects representing the bounding boxes of the extracted lineless tables, and a string indicating the priority side.
    """
    lineless_bboxes = []

    captions = []
    for block in cur_page.text_blocks:
        full_text = " ".join(
            span.text for line in block.lines for span in line.spans
        ).strip()
        if full_text.lower().startswith(
            ("tabela", "tab.", "tabele", "table", "tables")
        ):
            captions.append({"bbox": fitz.Rect(block.bbox), "text": full_text})

    for cap in captions:
        is_already_handled = False
        for ext_bbox in existing_table_bboxes:
            if (
                abs(cap["bbox"].y1 - ext_bbox.y0) < 60
                or abs(cap["bbox"].y0 - ext_bbox.y1) < 60
            ):
                is_already_handled = True
                break
        if is_already_handled:
            continue

        down_y0 = cap["bbox"].y1
        down_y1 = down_y0 + 350
        for block in cur_page.text_blocks:
            b_rect = fitz.Rect(block.bbox)
            if b_rect.y0 > down_y0 + 5:
                full_text = " ".join(
                    span.text for line in block.lines for span in line.spans
                ).strip()

                is_paragraph = (
                    b_rect.width > cur_page.width * 0.55 and len(block.lines) >= 2
                ) or (b_rect.width > cur_page.width * 0.70)
                is_caption = full_text.lower().startswith(
                    ("rys", "tab", "fot", "wykres", "źródło", "zródło", "source")
                )
                is_legend = full_text.lower().startswith(
                    "gdzie"
                )  # <--- NOWY HAMULEC NA WZORY

                if is_paragraph or is_caption or is_legend:
                    down_y1 = min(down_y1, b_rect.y0 - 15)
                    break

        up_y1 = cap["bbox"].y0
        up_y0 = up_y1 - 350
        for block in reversed(cur_page.text_blocks):
            b_rect = fitz.Rect(block.bbox)
            if b_rect.y1 < up_y1 - 5:
                full_text = " ".join(
                    span.text for line in block.lines for span in line.spans
                ).strip()

                is_paragraph = (
                    b_rect.width > cur_page.width * 0.55 and len(block.lines) >= 2
                ) or (b_rect.width > cur_page.width * 0.70)
                is_caption = full_text.lower().startswith(
                    ("rys", "tab", "fot", "wykres", "źródło", "zródło", "source")
                )
                is_legend = full_text.lower().startswith(
                    "gdzie"
                )  # <--- NOWY HAMULEC NA WZORY

                if is_paragraph or is_caption or is_legend:
                    up_y0 = max(up_y0, b_rect.y1 + 15)
                    break

        if priority_side == "below":
            areas_to_check = [
                fitz.Rect(0, up_y0, cur_page.width, up_y1),
                fitz.Rect(0, down_y0, cur_page.width, down_y1),
            ]
        else:
            areas_to_check = [
                fitz.Rect(0, down_y0, cur_page.width, down_y1),
                fitz.Rect(0, up_y0, cur_page.width, up_y1),
            ]

        table_extracted = False

        for table_rect in areas_to_check:
            if table_extracted:
                break
            if table_rect.height < 20:
                continue

            raw_words = page.get_text("words", clip=table_rect)
            if not raw_words:
                continue

            words = []
            for w in raw_words:
                center_y = (w[1] + w[3]) / 2
                if table_rect.y0 <= center_y <= table_rect.y1:
                    words.append(w)

            if not words:
                continue

            words.sort(key=lambda w: w[1])
            top_y = words[0][1]
            header_words = [w for w in words if w[1] < top_y + 15]
            header_words.sort(key=lambda w: w[0])

            col_dividers = [0]
            last_x1 = -999
            is_first = True
            for w in header_words:
                if is_first:
                    is_first = False
                    last_x1 = w[2]
                    continue

                if w[0] > last_x1 + 10:
                    col_dividers.append(w[0] - 5)
                last_x1 = max(last_x1, w[2])
            col_dividers.append(cur_page.width)

            num_cols = len(col_dividers) - 1
            if num_cols < 2:
                continue

            words.sort(key=lambda w: (w[1], w[0]))
            lines = []
            current_line = []
            last_y = -999
            for w in words:
                if abs(w[1] - last_y) > 5:
                    if current_line:
                        current_line.sort(key=lambda x: x[0])
                        lines.append(current_line)
                    current_line = [w]
                    last_y = w[1]
                else:
                    current_line.append(w)
            if current_line:
                current_line.sort(key=lambda x: x[0])
                lines.append(current_line)

            grid = []
            for line in lines:
                row_data = [""] * num_cols
                for w in line:
                    c_idx = num_cols - 1
                    for c in range(num_cols):
                        if w[0] < col_dividers[c + 1]:
                            c_idx = c
                            break
                    row_data[c_idx] += fix_latex(w[4]) + " "
                grid.append([cell.strip() for cell in row_data])

            final_data = []
            for row in grid:
                if not any(row):
                    continue
                if not final_data:
                    final_data.append(row)
                    continue

                if row[0] == "":
                    for c in range(num_cols):
                        if row[c]:
                            prev = final_data[-1][c]
                            if prev and prev.endswith("-"):
                                final_data[-1][c] = prev[:-1] + row[c]
                            elif prev:
                                final_data[-1][c] = prev + " " + row[c]
                            else:
                                final_data[-1][c] = row[c]
                else:
                    final_data.append(row)

            total_cells = len(final_data) * num_cols if final_data else 0
            if total_cells > 0:
                filled_cells = sum(
                    1 for row in final_data for cell in row if cell != ""
                )
                if (filled_cells / total_cells) < 0.20:
                    continue

            actual_y0 = min(w[1] for w in words)
            actual_y1 = max(w[3] for w in words)
            actual_x0 = min(w[0] for w in words)
            actual_x1 = max(w[2] for w in words)
            found_bbox = fitz.Rect(actual_x0, actual_y0, actual_x1, actual_y1)

            lineless_bboxes.append(found_bbox)
            cur_page.tables.append(
                TableInfo(
                    bbox=(found_bbox.x0, found_bbox.y0, found_bbox.x1, found_bbox.y1),
                    row_count=len(final_data),
                    col_count=num_cols,
                    description=cap["text"],
                    data=final_data,
                    table_type="lineless",
                )
            )
            table_extracted = True

    return lineless_bboxes, priority_side
