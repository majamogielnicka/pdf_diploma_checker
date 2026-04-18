'''
Tutaj znajdują się funkcje odpowiedzialne za ekstrakcję danych z PDF do jsona (surprise, surprise).
W przyszłości proponuje to przenieść jako metody struktury zamiast oddzielnych funkcji do wszystkiego
'''
import os
import fitz  # PyMuPDF
import statistics
from typing import Dict
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
REDACTION_DIR = PROJECT_ROOT / "src" / "redaction"

sys.path.insert(0, str(REDACTION_DIR))

from src.analysis.extraction.bare_struct import DocumentData, PageData, TextBlock, TextLine, TextSpan, ImageInfo, TableInfo, HeaderData, TocData, TocEntry


# Tryb debugu:
# 0 - domyślny tryb, program działakorzystając z /thesis
# 1 - tryb debugowania, ułatwia pracę nad konkretną funkcjonalnością, korzysta z /redaction_debug
# TODO: dodać więcej przykładowych plików pdf do folderu /redaction_debug
# Format nazwy pdfa: <aspekt_do_sprawdzenia>_example.pdf
debug_mode = 0
debug_type = "table" # zmiana trybu debugowania (wpisać interesujący nas aspekt)
debug_path = "pdf_diploma_checker/src/redaction/redaction_debug/{debug_type}_example.pdf"

#uzywam dekoratora dataclass bo:
#ma fajne automatyczne funkcje jak tworzenie __init__ automatycznie
#jest duzo bardziej czytelny (#team_c++)
#ma wbudowana funkcje asdict() (potem sie przyda do jsona)

    
def calculate_margins(blocks, width, height) -> Dict[str, float]:
    if not blocks:
        return {"top": 0.0, "bottom": 0.0, "left": 0.0, "right": 0.0}

    # inicjalizacja marginesów do optymalizacji (początkowo lewy maksymalnie po prawej, dolny maksymalnie na górze itd)
    margin_top_buf = height # odczytane koordynaty są od góry do dołu (góra to y=0, dół to y=wysokość_dokumentu)
    margin_bottom_buf = 0   
    margin_left_buf = width
    margin_right_buf = 0

    for b in blocks: #iterowanie po rozmiarach każdego z bloczków, szukanie min/max wartości
        x0, y0, x1, y1 = b["bbox"]
        if x0 < margin_left_buf: margin_left_buf = x0
        if y0 < margin_top_buf: margin_top_buf = y0
        if x1 > margin_right_buf: margin_right_buf = x1
        if y1 > margin_bottom_buf: margin_bottom_buf = y1

    # wyznaczenie faltycznych wielkości marginesów
    margin_top = margin_top_buf
    margin_bottom = height - margin_bottom_buf
    margin_left = margin_left_buf
    margin_right = width - margin_right_buf
        
    return {
        "top": margin_top,
        "bottom": margin_bottom,
        "left": margin_left,
        "right": margin_right
    }

# Analizza justowania
def analyze_line_alignment(line: TextLine, page_width: float, margins: Dict[str, float], tolerance: float = 5.0) -> tuple:
    l_x0, _, l_x1, _ = line.bbox
    
    # Obszar tekstu wyznaczony przez marginesy
    content_start = margins["left"]
    content_end = page_width - margins["right"]
    
    dist_left = abs(l_x0 - content_start)
    dist_right = abs(l_x1 - content_end)
    
    # Sprawdzenie czy dotyka obu marginesów
    is_at_left = dist_left <= tolerance
    is_at_right = dist_right <= tolerance
    
    # Obliczanie odstępów między spanami
    gaps = []
    if len(line.spans) > 1:
        for i in range(len(line.spans) - 1):
            gap = line.spans[i+1].bbox[0] - line.spans[i].bbox[2]
            if gap > 0: 
                gaps.append(gap)
    
    is_consistent = True
    if len(gaps) > 1:
        # Sprawdzemie justowania poprzez odchylenie standardowe
        std_dev = statistics.stdev(gaps)
        if std_dev > 1.0: # próg czułości 
            is_consistent = False

    # Logika rozpoznawania stylu
    if is_at_left and is_at_right and not is_consistent:
        return "justified", False, dist_right # justowanie niepełne (błędne bo nierówne odstępy)
    elif is_at_left and is_at_right: 
        return "justified", True, dist_right # justowanie pełne
    elif abs(dist_left - dist_right) <= tolerance:
        return "center", True, dist_right # tekst wyśrodkowany
    elif is_at_right: 
        return "right", True, dist_right # tekst wyrównany do prawej
    else:
        return "left", True, dist_right # tekst wyrównany do lewej 
    
def fix_latex(text):
    replace = { #Słownik znaków do podmiany.
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
    }
    for wrong, right in replace.items():
        text = text.replace(wrong, right)
    return text

def find_table_description(table_bbox, text_blocks, priority_side=None):
    #TODO: poprawić tak, żeby nie wykrywało obrazów w spisie treści, bibliografii itd (ale to jak już będziemy mieli spis treści, bibliografie itd)
    x0, y0, x1, y1 = table_bbox
    # Rozdzielamy potencjalne opisy na górę i dół oraz sprawdzamy słowa kluczowe
    kw_matches = {"above": [], "below": []}
    other_matches = {"above": [], "below": []}

    for block in text_blocks:
        bx0, by0, bx1, by1 = block.bbox
        
        # 1. Szukanie odległości pionowej 
        is_close_above =  abs(by1 - y0) < 40  # Nad tabelą
        is_close_below =  abs(by0 - y1) < 60  # Pod tabelą
        
        if is_close_above or is_close_below:
            full_text = " ".join(span.text for line in block.lines for span in line.spans).strip()
            side = "above" if is_close_above else "below"
            
            # 2. Szukanie czy tekst zaczyna się od "Tabela" lub "Tab."
            if full_text.lower().startswith(("tabele", "tabela", "tab.", "table", "tab")):
                kw_matches[side].append(full_text)
            else:
                other_matches[side].append(full_text)

    # Ustalenie kolejności sprawdzania
    primary = priority_side if priority_side else "above"
    secondary = "below" if primary == "above" else "above"

    # Priorytetyzacja:
    # 1. Słowo kluczowe na preferowanej stronie
    if kw_matches[primary]: return kw_matches[primary][0], primary
    # 2. Słowo kluczowe na jakiejkolwiek stronie
    if kw_matches[secondary]: return kw_matches[secondary][0], secondary
    # 3. Zwykły tekst na preferowanej stronie
    if other_matches[primary]: return other_matches[primary][0], primary
    # 4. Zwykły tekst na jakiejkolwiek stronie
    if other_matches[secondary]: return other_matches[secondary][0], secondary

    return "", priority_side

def find_image_description(image_bbox, text_blocks, priority_side=None):
    x0, y0, x1, y1 = image_bbox
    kw_matches = {"above": [], "below": []}
    other_matches = {"above": [], "below": []}

    for block in text_blocks:
        bx0, by0, bx1, by1 = block.bbox
        
        # Tolerancja odległości (obrazy często mają podpisy ciut dalej niż tabele)
        is_close_above = abs(by1 - y0) < 40
        is_close_below = abs(by0 - y1) < 40
        
        if is_close_above or is_close_below:
            full_text = " ".join(span.text for line in block.lines for span in line.spans).strip()
            if not full_text: continue
            
            side = "above" if is_close_above else "below"
            
            # Słowa kluczowe dla obrazów
            img_keywords = ("rysunek", "rys.", "fot.", "ilustracja", "wykres", "rycina", "schemat", "diagram", "grafika", "figure", "fig.", "photo", "img", "image", "schema", "chart", "plot")
            
            if full_text.lower().startswith(img_keywords):
                kw_matches[side].append(full_text)
            else:
                other_matches[side].append(full_text)

    # Obrazy zwykle mają podpisy na dole
    primary = priority_side if priority_side else "below"
    secondary = "above" if primary == "below" else "below"

    # Logika priorytetów (identyczna jak w tabelach):
    if kw_matches[primary]: return kw_matches[primary][0], primary
    if kw_matches[secondary]: return kw_matches[secondary][0], secondary
    if other_matches[primary]: return other_matches[primary][0], primary
    if other_matches[secondary]: return other_matches[secondary][0], secondary

    return "", None

def extract_tables(page: fitz.Page, drawings: list, cur_page: PageData, priority_side=None) -> tuple[list, str]:
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
    #TODO: znajdywanie tabel typu APA czyli, takich z niestandardowym obramowaniem bez linii poziomych albo jakichkolwiek linii. ogólna poprawa działania funkcji
    #znajdowanie tabel, wyciąganie danych i zapisywanie do list
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

        #usuwa entery i zamienia na spacje, można potem usunąć jakbyśmy chcieli widzieć gdzie są entery
        cleaned_data = [ 
            [cell.replace('\n', ' ').strip() if cell else "" for cell in row]
            for row in extracted_data
        ]

        #zabezpieczenie przed zapisywaniem wykresów jako tabelek
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
            
        description, found_side = find_table_description(tab.bbox, cur_page.text_blocks, priority_side)
        if description and priority_side is None:
            priority_side = found_side

        table_bboxes.append(fitz.Rect(tab.bbox))
        cur_page.tables.append(TableInfo(
            bbox=tab.bbox,
            row_count=tab.row_count,
            col_count=tab.col_count,
            description=description,
            data=cleaned_data
        ))      

    return table_bboxes, priority_side

def extract_apa_tables(page: fitz.Page, drawings: list, cur_page: PageData, existing_table_bboxes: list, priority_side=None) -> tuple[list, str]:
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
        if i in used_lines: continue
        current_group = [line]
        used_lines.add(i)
        
        for j, other_line in enumerate(horizontal_lines[i+1:], start=i+1):
            if j in used_lines: continue
            if abs(line.x0 - other_line.x0) < 25 and abs(line.x1 - other_line.x1) < 25:
                if other_line.y0 - current_group[-1].y0 < 500:
                    current_group.append(other_line)
                    used_lines.add(j)
                    
        if len(current_group) >= 2:
            top_y = current_group[0].y0 - 10
            bottom_y = current_group[-1].y1 + 10
            min_x = min(l.x0 for l in current_group) - 10
            max_x = max(l.x1 for l in current_group) + 10
            apa_rect = fitz.Rect(min_x, top_y, max_x, bottom_y)
            grouped_table_rects.append(apa_rect)

    for apa_rect in grouped_table_rects:
        is_duplicate = False
        for existing_rect in existing_table_bboxes:
            intersect = apa_rect & existing_rect
            if intersect.is_valid and not intersect.is_empty:
                overlap_area = intersect.width * intersect.height
                if overlap_area / min(apa_rect.width * apa_rect.height, existing_rect.width * existing_rect.height + 0.001) > 0.15:
                    is_duplicate = True
                    break
        if is_duplicate:
            continue


        words = page.get_text("words", clip=apa_rect)
        if not words: continue
        
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
                    if w[0] < col_dividers[c+1]:
                        c_idx = c
                        break
                row_data[c_idx] += fix_latex(w[4]) + " "
            grid.append([cell.strip() for cell in row_data])
            
        final_data = []
        for row in grid:
            if not any(row): continue
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
                
        description, found_side = find_table_description(apa_rect, cur_page.text_blocks, priority_side)
        if description and priority_side is None:
            priority_side = found_side

        apa_bboxes.append(apa_rect)
        cur_page.tables.append(TableInfo(
            bbox=(apa_rect.x0, apa_rect.y0, apa_rect.x1, apa_rect.y1),
            row_count=len(final_data),
            col_count=num_cols,
            description=description,
            data=final_data,
            table_type="apa" 
        ))      

    return apa_bboxes, priority_side

def extract_lineless_tables(page: fitz.Page, cur_page: PageData, existing_table_bboxes: list, priority_side=None) -> tuple[list, str]:
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
        full_text = " ".join(span.text for line in block.lines for span in line.spans).strip()
        if full_text.lower().startswith(("tabela", "tab.", "tabele", "table", "tables")):
            captions.append({"bbox": fitz.Rect(block.bbox), "text": full_text})
            
    for cap in captions:
        is_already_handled = False
        for ext_bbox in existing_table_bboxes:
            if abs(cap["bbox"].y1 - ext_bbox.y0) < 60 or abs(cap["bbox"].y0 - ext_bbox.y1) < 60:
                is_already_handled = True
                break
        if is_already_handled:
            continue
            
        down_y0 = cap["bbox"].y1
        down_y1 = down_y0 + 350
        for block in cur_page.text_blocks:
            b_rect = fitz.Rect(block.bbox)
            if b_rect.y0 > down_y0 + 5: 
                full_text = " ".join(span.text for line in block.lines for span in line.spans).strip()
                
                is_paragraph = (b_rect.width > cur_page.width * 0.55 and len(block.lines) >= 2) or (b_rect.width > cur_page.width * 0.70)
                is_caption = full_text.lower().startswith(("rys", "tab", "fot", "wykres", "źródło", "zródło", "source"))
                is_legend = full_text.lower().startswith("gdzie") # <--- NOWY HAMULEC NA WZORY
                
                if is_paragraph or is_caption or is_legend:
                    down_y1 = min(down_y1, b_rect.y0 - 15)
                    break
                    
        up_y1 = cap["bbox"].y0
        up_y0 = up_y1 - 350
        for block in reversed(cur_page.text_blocks):
            b_rect = fitz.Rect(block.bbox)
            if b_rect.y1 < up_y1 - 5:
                full_text = " ".join(span.text for line in block.lines for span in line.spans).strip()
                
                is_paragraph = (b_rect.width > cur_page.width * 0.55 and len(block.lines) >= 2) or (b_rect.width > cur_page.width * 0.70)
                is_caption = full_text.lower().startswith(("rys", "tab", "fot", "wykres", "źródło", "zródło", "source"))
                is_legend = full_text.lower().startswith("gdzie") # <--- NOWY HAMULEC NA WZORY
                
                if is_paragraph or is_caption or is_legend:
                    up_y0 = max(up_y0, b_rect.y1 + 15)
                    break

        if priority_side == "below":
            areas_to_check = [
                fitz.Rect(0, up_y0, cur_page.width, up_y1),
                fitz.Rect(0, down_y0, cur_page.width, down_y1)
            ]
        else:
            areas_to_check = [
                fitz.Rect(0, down_y0, cur_page.width, down_y1),
                fitz.Rect(0, up_y0, cur_page.width, up_y1)
            ]

        table_extracted = False

        for table_rect in areas_to_check:
            if table_extracted: break
            if table_rect.height < 20: continue
            
            raw_words = page.get_text("words", clip=table_rect)
            if not raw_words: continue
            
            words = []
            for w in raw_words:
                center_y = (w[1] + w[3]) / 2
                if table_rect.y0 <= center_y <= table_rect.y1:
                    words.append(w)
                    
            if not words: continue
            
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
                        if w[0] < col_dividers[c+1]:
                            c_idx = c
                            break
                    row_data[c_idx] += fix_latex(w[4]) + " "
                grid.append([cell.strip() for cell in row_data])
                
            final_data = []
            for row in grid:
                if not any(row): continue
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
                    
            actual_y0 = min(w[1] for w in words)
            actual_y1 = max(w[3] for w in words)
            actual_x0 = min(w[0] for w in words)
            actual_x1 = max(w[2] for w in words)
            found_bbox = fitz.Rect(actual_x0, actual_y0, actual_x1, actual_y1)

            lineless_bboxes.append(found_bbox)
            cur_page.tables.append(TableInfo(
                bbox=(found_bbox.x0, found_bbox.y0, found_bbox.x1, found_bbox.y1),
                row_count=len(final_data),
                col_count=num_cols,
                description=cap["text"],
                data=final_data,
                table_type="lineless"
            ))
            table_extracted = True

    return lineless_bboxes, priority_side

def extract_vector_graphics(page: fitz.Page, drawings: list, page_index: int, table_bboxes: list, cur_page: PageData, priority_side=None) -> str:
    """
    Extracts vector graphics from a PDF page, merges adjacent shapes, and saves them as images.
    
    Args:
        page (fitz.Page): The PDF page.
        drawings (list): A list of raw vector drawings from the page.
        page_index (int): The index of the current page, used for generating image filenames.
        table_bboxes (list): A list of table bounding boxes to avoid extracting table borders.
        cur_page (PageData): The data object for the current page where image metadata is appended.
        priority_side (str, optional): The preferred side (above/below) to look for descriptions.

        
    Returns:
        return priority_side(str)
    """
    if not drawings:
        return priority_side

    content_width = cur_page.width - cur_page.margins.get("left", 0) - cur_page.margins.get("right", 0)
    if content_width <= 50:
        content_width = page.rect.width * 0.8

    vector_bboxes = []
    for d in drawings:
       
       color = d.get("color")
       fill = d.get("fill")
       
       if color is None and fill is None:
           continue
       if (color is None or (len(color) in (1, 3) and min(color) >= 0.98)) and (fill is None or (len(fill) in (1, 3) and min(fill) >= 0.98)):
           continue
       
       rect = fitz.Rect(d["rect"])
       if max(rect.width, rect.height) <= 2:
           continue

       is_orthogonal = True
       is_rect_only = True          
       for item in d.get("items", []):
           if item[0] == "l":
               is_rect_only = False                  
               p1, p2 = item[1], item[2]
               if abs(p1.x - p2.x) > 2 and abs(p1.y - p2.y) > 2:
                   is_orthogonal = False
                   break
           elif item[0] in ("c", "q"):
               is_rect_only = False                  
               is_orthogonal = False
               break
           elif item[0] != "re":
               is_rect_only = False              
               
       is_inside_table = False
       for t_bbox in table_bboxes:
           expanded_t_bbox = t_bbox + (-10, -10, 10, 10)
           intersect = rect & expanded_t_bbox
           if intersect.is_valid and not intersect.is_empty:
               if (intersect.width * intersect.height) / (rect.width * rect.height + 0.001) > 0.8:
                   is_inside_table = True
                   break

       if is_inside_table and is_orthogonal:
           continue

       has_dark_stroke = False
       if color is not None:
           if len(color) in (1, 3) and sum(color)/len(color) <= 0.85:
               has_dark_stroke = True
           elif len(color) == 4 and max(color) >= 0.15: 
               has_dark_stroke = True

       has_dark_fill = False
       if fill is not None:
           if len(fill) in (1, 3) and sum(fill)/len(fill) <= 0.85:
               has_dark_fill = True
           elif len(fill) == 4 and max(fill) >= 0.15: 
               has_dark_fill = True
               
       is_pale_shape = not has_dark_stroke and not has_dark_fill

       if is_pale_shape and is_rect_only:
           continue
           
       is_text_formatting = False
       lines_inside = 0
       expanded_rect = rect + (-5, -5, 5, 5)           
       for text_block in cur_page.text_blocks:
           for line in text_block.lines:
               t_rect = fitz.Rect(line.bbox)
               if expanded_rect.intersects(t_rect):
                   lines_inside += 1
                   
                   if rect.height <= 3 and rect.x0 >= t_rect.x0 - 5 and rect.x1 <= t_rect.x1 + 5:
                       is_text_formatting = True
                   
       if lines_inside > 0:
           if is_pale_shape:
               is_text_formatting = True
           elif rect.height <= 5 and rect.width < 150: 
               is_text_formatting = True
       elif is_pale_shape and is_rect_only:
           is_text_formatting = True                   
           
       if not is_text_formatting:
           vector_bboxes.append(rect)
    
    merged_bboxes = vector_bboxes.copy()
    changed = True
    
    while changed:
        changed = False
        new_merged = []
        
        while len(merged_bboxes) > 0:
            current = merged_bboxes.pop(0)
            expanded_current = current + (-80, -80, 80, 80) 
            
            i = 0
            while i < len(merged_bboxes):
                if expanded_current.intersects(merged_bboxes[i]):
                    current = current | merged_bboxes[i]
                    expanded_current = current + (-80, -80, 80, 80)
                    merged_bboxes.pop(i)
                    changed = True
                else:
                    i += 1
            new_merged.append(current)
        merged_bboxes = new_merged

    MIN_PHYSICAL_WIDTH = 40
    MIN_PHYSICAL_HEIGHT = 20
    
    for i in range(len(merged_bboxes)):
        bbox = merged_bboxes[i]
        
        if bbox.width > MIN_PHYSICAL_WIDTH and bbox.height > MIN_PHYSICAL_HEIGHT:
            changed_text = True
            while changed_text:
                changed_text = False
                search_area = bbox + (-35, -5, 35, 20) 
                new_bbox = bbox
                
                for t_block in cur_page.text_blocks:
                    for line in t_block.lines:
                        t_rect = fitz.Rect(line.bbox)
                        if search_area.intersects(t_rect) and not bbox.contains(t_rect):
                            
                            if t_rect.width > content_width * 0.40: 
                                continue
                                
                            line_text = " ".join([s.text for s in line.spans]).strip()
                            
                            if line_text.lower().startswith(("rys", "tab", "fot", "wykres", "schemat", "figure", "fig")):
                                continue
                                
                            if line_text.endswith(".") and t_rect.y1 <= bbox.y0 + 20:
                                continue
                                
                            new_bbox = new_bbox | t_rect
                            changed_text = True
                bbox = new_bbox
            
            merged_bboxes[i] = bbox + (-5, -5, 5, 5) 

    for i, bbox in enumerate(merged_bboxes):
        if bbox.width > MIN_PHYSICAL_WIDTH and bbox.height > MIN_PHYSICAL_HEIGHT:
            aspect_ratio = bbox.width / bbox.height
            
            if aspect_ratio < 25.0 and aspect_ratio > 0.05:
                
                is_invalid = False
                for t_bbox in table_bboxes:
                    intersect = bbox & t_bbox 
                    if intersect.is_valid and not intersect.is_empty:
                        intersect_area = intersect.width * intersect.height
                        bbox_area = bbox.width * bbox.height
                        t_bbox_area = t_bbox.width * t_bbox.height
                        
                        if t_bbox_area > 0 and (intersect_area / t_bbox_area) > 0.50:
                            is_invalid = True
                            break
                        if bbox_area > 0 and (intersect_area / bbox_area) > 0.80:
                            is_invalid = True
                            break
                                
                if is_invalid:
                    continue
                
                bbox = bbox.intersect(page.rect)
                if not bbox.is_valid or bbox.is_empty:
                    continue
                
                description, found_side = find_image_description(
                (bbox.x0, bbox.y0, bbox.x1, bbox.y1), 
                    cur_page.text_blocks, 
                    priority_side
                )
        
                if description and priority_side is None:
                    priority_side = found_side

                pix = page.get_pixmap(clip=bbox)
                img_path = f"images/p{page_index}_vec_{i}.png"
                pix.save(img_path)
                
                cur_page.images.append(ImageInfo(
                    path=img_path,
                    bbox=(bbox.x0, bbox.y0, bbox.x1, bbox.y1),
                    width=pix.width,
                    height=pix.height,
                    image_type="vector",
                    description=description
                ))

    return priority_side

def extract_raster_images(blocks: list, drawings: list, page_width: float, page_height: float, page_index: int, cur_page: PageData, priority_side=None) -> str:
    """
    Extracts raster images from PDF blocks, filters them (removes backgrounds, small icons), and saves them to images.
    
    Args:
        blocks (list): A list of blocks extracted from page.get_text("dict")["blocks"].
        drawings (list): A list of vector drawings on the page, used for collision detection.
        page_width (float): The width of the page.
        page_height (float): The height of the page.
        page_index (int): The index of the current page, used for generating image filenames.
        cur_page (PageData): The data object for the current page where extracted image metadata is appended.
        priority_side (str, optional): The preferred side (above/below) to look for descriptions.
        
    Returns:
        str: The updated priority_side for images.
    """
    for block in blocks:
        if block["type"] == 1:
            x0, y0, x1, y1 = block["bbox"]
            phys_width = x1 - x0
            phys_height = y1 - y0
            img_rect = fitz.Rect(block["bbox"])

            MIN_PHYSICAL_WIDTH = 20
            MIN_PHYSICAL_HEIGHT = 20
            
            if phys_width < MIN_PHYSICAL_WIDTH or phys_height < MIN_PHYSICAL_HEIGHT:
                continue

            if phys_width < 40 and phys_height < 40:
                is_inline_with_text = False
                for t_block in cur_page.text_blocks:
                    t_rect = fitz.Rect(t_block.bbox) + (-2, -2, 2, 2)
                    if img_rect.intersects(t_rect):
                        is_inline_with_text = True
                        break
                        
                is_in_drawing = False
                for d in drawings:
                    d_rect = fitz.Rect(d["rect"])
                    if d_rect.width < page_width * 0.9 and d_rect.height < page_height * 0.9:
                        if img_rect.intersects(d_rect):
                            is_in_drawing = True
                            break
                            
                if is_inline_with_text and not is_in_drawing:
                    continue
                    
                if not is_in_drawing and block["width"] < 150 and block["height"] < 150:
                    continue

            if phys_height > 0:
                aspect_ratio = phys_width / phys_height
                if aspect_ratio > 15.0 or aspect_ratio < 0.15:
                    continue
                
                if phys_height < 35 and aspect_ratio > 2.5:
                    continue

            try:
                pix = fitz.Pixmap(block["image"])
                if pix.is_unicolor:
                    continue
            except:
                pass

            is_background = False
            if img_rect.height < 60:
                for t_block in cur_page.text_blocks:
                    for line in t_block.lines:
                        t_rect = fitz.Rect(line.bbox)
                        intersect = img_rect & t_rect
                        if intersect.is_valid and not intersect.is_empty:
                            overlap_area = intersect.width * intersect.height
                            img_area = img_rect.width * img_rect.height
                            if overlap_area / img_area > 0.6:
                                is_background = True
                                break
                    if is_background:
                        break
                        
            if is_background:
                continue
            
            description, found_side = find_image_description(block["bbox"], cur_page.text_blocks, priority_side)
            if description and priority_side is None:
                priority_side = found_side

            ext = block.get("ext", "png")
            img_path = f"images/p{page_index}_b{block['number']}.{ext}"

            # zapisywanie obrazów
            with open(img_path, "wb") as img_file:
                img_file.write(block["image"])
                
            cur_page.images.append(ImageInfo(
                path=img_path,
                bbox=block["bbox"],
                width=block["width"],
                height=block["height"],
                image_type="raster",
                description=description
            ))
            
    return priority_side

def extractPDF(file_path: str) -> DocumentData:
    current_span_id = 0
    if not os.path.exists(file_path):
        #TODO:tutaj jakis wyjatek
        print(f"plik nie istnieje")
        return
    
    #sprawdzenie czy mamy folder "images", jeśli nie to tworzymy taki
    os.makedirs("images", exist_ok=True)

    #usuwanie obrazów z poprzedniego sprawdzania, żeby nie było chaosu
    for filename in os.listdir("images"):
        file_to_delete = os.path.join("images", filename)
        try:
            if os.path.isfile(file_to_delete):
                os.remove(file_to_delete)
        except Exception as e:
            print(f"Nie udało się usunąć starego pliku {file_to_delete}: {e}")
    
    #TODO: dalsza walidacja
    doc = fitz.open(file_path)
    metadata = doc.metadata
    document_data = DocumentData(metadata=metadata)

    # Priorytet dla wykrywania tabel i obrazów na górze lub dole (z reguły jest to stałe dla pracy)
    detected_priority = None
    detected_img_priority = "below"
    #Do wykrycia interlinii
    all_spacings = []

    for page_index, page in enumerate(doc):
        raw_dict = page.get_text("dict")
        word_list = page.get_text("words")
        p_width = page.rect.width
        p_height = page.rect.height

        page_format, page_orientation = check_page_format(p_width, p_height)

        blank_page = True

        cur_page = PageData(
            number=page_index + 1,
            width=p_width,
            height=p_height,
            margins=calculate_margins(raw_dict["blocks"], p_width, p_height),
            text_blocks=[],
            images=[],
            orientation = page_orientation,
            format = page_format,
            is_blank = True
        )

        drawings = page.get_drawings()

        # table_bboxes = extract_tables(page, drawings, cur_page)
        last_block_btmline = None #Ostatnia linia w bloku - do interlinii
        # Najpierw wyciągamy wszystkie bloki tekstowe ze strony
        for block in raw_dict["blocks"]:
            #typ 0 to tekst, typ 1 to obraz
            if block["type"] == 0:
                is_ftr = is_footer(block, p_height, page_index + 1)
                text_block, last_block_btmline, current_span_id = parse_text_block(block, word_list, p_width, cur_page.margins, last_block_btmline, current_span_id, all_spacings, is_ftr)
                if text_block.lines:
                    cur_page.text_blocks.append(text_block)
                    if not is_ftr:
                        blank_page = False

        # Dopiero po zebraniu tekstu procesujemy obrazy rastrowe, aby opisy pod nimi były już dostępne  
        detected_img_priority = extract_raster_images(
            blocks=raw_dict["blocks"],
            drawings=drawings,
            page_width=p_width,
            page_height=p_height,
            page_index=page_index,
            cur_page=cur_page,
            priority_side=detected_img_priority
        )

        if all_spacings: #Znajdywanie średniej interlinii wykorzystywanej w pliku
            for s in range(len(all_spacings)):
                all_spacings[s] = round(all_spacings[s], 1)
            mode = statistics.mode(all_spacings)
            document_data.metadata["avarge_line_spacing"] = mode

        table_bboxes, detected_priority = extract_tables(page, drawings, cur_page, detected_priority)

        apa_bboxes, detected_priority = extract_apa_tables(page, drawings, cur_page, table_bboxes, detected_priority)

        existing_for_lineless = table_bboxes + apa_bboxes
        lineless_bboxes, detected_priority = extract_lineless_tables(page, cur_page, existing_for_lineless, detected_priority)

        all_table_bboxes = table_bboxes + apa_bboxes + lineless_bboxes
        if all_table_bboxes: 
            blank_page = False
        detected_img_priority = extract_vector_graphics(page, drawings, page_index, all_table_bboxes, cur_page, detected_img_priority)    
        if len(cur_page.images) > 0:
            blank_page = False
        cur_page.is_blank = blank_page
        document_data.pages.append(cur_page)
    document_data.toc = extract_TOC(doc, document_data.pages)
    doc.close()
    return document_data

#Niestety używanie samego dicta powoduje, że nie można dokładnie rozdzielić spanów na same słowa z informacją
#o ich położeniu. Natomiast sama lista słów zwraca dokładne koordynaty słowa, ale nie pozwala na
#detekcję czcionki, itd. W związku z tym użyto zarówno dicta jak i listy słów, aby połączyć korzyści.
def parse_text_block(raw_block: dict, word_list:list, page_width: float, margins: Dict[str, float], last_block_btmline: float, current_span_id: int, all_spacings: list, is_ftr:bool) -> tuple[TextBlock, float, int]:
    lines = []
    block_words = []
    prev_bottomline = last_block_btmline

    #Sprawdzanie, które słowa są w środk danego bloku, żeby nie sprawdzać każdego słowa
    #na stronie czy nie należy do danego spana

    for x in word_list:
        if x[5] == raw_block["number"]:
            block_words.append(x)

    for raw_line in raw_block["lines"]:
        spans = []
        max_font_size = 0.0 #Do znalezienia słowa o największej czcionce w linijce.

        for raw_span in raw_line["spans"]:
            if not raw_span["text"].strip():
                continue
            
            s_bbox = raw_span["bbox"]
            span_words = []

            if raw_span["size"] > max_font_size:
                max_font_size = raw_span["size"]

            for x in block_words:
                #Sprawdzanie czy dane słowo należy do spanu z małym marginesem błędu (0.2), w razie
                #problemów można zwiększyć
                if (x[0] >= s_bbox[0] - 0.2 and x[1]>= s_bbox[1]-0.2 and x[2]<=s_bbox[2]+0.2 and x[3]<=s_bbox[3]+0.2):
                    span_words.append(x)

            #obsluga flag
            flags = raw_span["flags"]

            if span_words:
                for x in span_words:
                    current_span_id += 1
                    spans.append(TextSpan(
                        span_id=current_span_id,
                        text=fix_latex(x[4]),
                        font=raw_span["font"],
                        size=round(raw_span["size"], 2),
                        color=raw_span["color"],
                        bold=bool(flags & 16),
                        italic=bool(flags & 2),
                        bbox=(x[0],x[1],x[2],x[3])
                    ))
            else:
                current_span_id += 1
                spans.append(TextSpan(
                    span_id=current_span_id,
                    text=fix_latex(raw_span["text"]),
                    font=raw_span["font"],
                    size=round(raw_span["size"], 2),
                    color=raw_span["color"],                        
                    bold=bool(flags & 16),
                    italic=bool(flags & 2),
                    bbox=raw_span["bbox"]
                ))

        
        if spans:
            spacing = None
            curr_bottomline = raw_line["bbox"][3]
            if prev_bottomline is not None:
                spacing = line_spacing(curr_bottomline, prev_bottomline, max_font_size)
                if not is_ftr:
                    if spacing > 0.5 and spacing <3.0:
                        all_spacings.append(spacing)
                    else:
                        spacing = None
                else:
                    spacing = None

            curr_line = TextLine(
                spans=spans,
                bbox=raw_line["bbox"],
                baseline=raw_line["wmode"],
                line_spacing=spacing
            )
            prev_bottomline = curr_bottomline
            # analiza justowania
            alignment, consistent, gap_toright = analyze_line_alignment(curr_line, page_width, margins)
            curr_line.alignement = alignment
            curr_line.spacing_consistency = consistent
            # curr_line.gap_to_r = gap_toright #debug
            lines.append(curr_line)
            
    return TextBlock(lines=lines, bbox=raw_block["bbox"], block_id=raw_block["number"], block_type="footer" if is_ftr else "text"), prev_bottomline, current_span_id

def check_page_format(width, height, tolerance: float = 10) -> str:

    if height<width:
        orientation = "pozioma"
    else:
        orientation = "pionowa"

    formats = {
        "A5": (420, 595),
        "A4": (595, 842),
        "A3": (842, 1191)
    }

    for name, (w,h) in formats.items():
        for name, (w, h) in formats.items():
            if (abs(width - w) <= tolerance and abs(height - h) <= tolerance) or (abs(width - h) <= tolerance and abs(height - w) <= tolerance):
                return name, orientation
            
    return "incorrect", orientation

def line_spacing(curr_line: float, prev_line: float, font_size: float) -> float | None:
    if prev_line is not None:
        return round((curr_line - prev_line)/font_size/1.2,2) #Z jakiegoś powodu trzeba przeskalować do 1.2 ??
    else:
        return None

def dominant_spacing(doc: fitz.Document) ->float:
    spacings = []
    for page in doc:
        blocks = page.get_text("dict")

def is_footer(raw_block: dict, page_height: float, page_num: int, threshold: float = 0.88) -> bool:
    bbox = raw_block["bbox"]

    if bbox[1]<(page_height)*0.88:
        return False

    text_content = ""
    for line in raw_block.get("lines", []):
        for span in line.get("spans", []):
            text_content+= span.get("text","")
    
    clean_text = text_content.lower().strip()#zmieniamy na male litery
    patterns = [
        rf"^{page_num}$",
        rf"strona\s+{page_num}$",
        rf"str\.\s*{page_num}$",
        rf"^{page_num}\s*/\s*\d+$",
        rf"^{page_num}\s+z\s+\d+$",
    ]
    for p in patterns:
        if re.search(p,clean_text):
            return True

    return False

def extract_TOC(doc: fitz.Document, pages: list[PageData]) -> TocData | None:
    """
    Funkcja do ekstrakcji spisu treści. 
    Zwraca obiekt TocData jeśli znaleziono spis, w przeciwnym razie None.
    """
    built_in_toc = doc.get_toc()
    if built_in_toc:
        entries = []
        for lvl, ttl, page_num in built_in_toc:
            entries.append(TocEntry(
                level=lvl,
                title=ttl.strip(),
                page=page_num,
                bbox=(0, 0, 0, 0)  
            ))
        return TocData(page_num=-1,entries=entries, text="Wykryto z metadanych"
        )

    keywords = [
        "spis treści", "spis tresci", 
        "table of contents", "contents", "toc"
    ]
    for page_obj in pages[:10]:
        full_page_text = ""
        potential_entries = []
        base_x = None  
        
        for block in page_obj.text_blocks:
            for line in block.lines:
                line_text = " ".join([span.text for span in line.spans]).strip()
                full_page_text += line_text + " "
                
                match = re.search(r"^\s*(.*?)\s*[\.\s·\-]{5,}\s*(\d+)\s*$", line_text)
                
                if match:
                    title, p_num = match.groups()
                    title_clean = title.strip()

                    current_x = line.bbox[0]
                    if base_x is None:
                        base_x = current_x
                    
                    gap_level = 1 + int(max(0, current_x - base_x) / 12)

                    num_match = re.match(r"^(\d+(?:\.\d+)*)\.?", title_clean)
                    dotted_level = 1
                    if num_match:
                        num_part = num_match.group(1)
                        dotted_level = num_part.count('.') + 1

                    final_level = max(gap_level, dotted_level)

                    potential_entries.append(TocEntry(
                        level=final_level, 
                        title=title_clean,
                        page=int(p_num),
                        bbox=line.bbox
                    ))

        page_text_lower = full_page_text.lower()
        has_keyword = any(word in page_text_lower for word in keywords)
        
        if (has_keyword and len(potential_entries) >= 2) or len(potential_entries) >= 5:
            return TocData(
                page_num=page_obj.number,
                entries=potential_entries,
                text=full_page_text[:500]  
            )
        
    return None