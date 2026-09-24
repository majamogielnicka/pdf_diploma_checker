import statistics
from typing import Dict
import re

from analysis.extraction.raw_extraction.bare_struct import (
    TextLine,
)



def calculate_margins(blocks, width, height) -> Dict[str, float]:
    """
    Calculates the page margins based on the bounding boxes of the provided text blocks
    relative to the total page dimensions.

    Args:
        blocks (list): A list of text blocks, each containing bounding box coordinates.
        width (float): The total width of the page.
        height (float): The total height of the page.

    Returns:
        Dict[str, float]: A dictionary containing the calculated 'top', 'bottom',
        'left', and 'right' margins. Returns 0.0 for all if no blocks are provided.
    """
    if not blocks:
        return {"top": 0.0, "bottom": 0.0, "left": 0.0, "right": 0.0}

    # inicjalizacja marginesów do optymalizacji (początkowo lewy maksymalnie po prawej, dolny maksymalnie na górze itd)
    margin_top_buf = height  # odczytane koordynaty są od góry do dołu (góra to y=0, dół to y=wysokość_dokumentu)
    margin_bottom_buf = 0
    margin_left_buf = width
    margin_right_buf = 0

    for b in (
        blocks
    ):  # iterowanie po rozmiarach każdego z bloczków, szukanie min/max wartości
        x0, y0, x1, y1 = b["bbox"]
        if x0 < margin_left_buf:
            margin_left_buf = x0
        if y0 < margin_top_buf:
            margin_top_buf = y0
        if x1 > margin_right_buf:
            margin_right_buf = x1
        if y1 > margin_bottom_buf:
            margin_bottom_buf = y1

    # wyznaczenie faltycznych wielkości marginesów
    margin_top = margin_top_buf
    margin_bottom = height - margin_bottom_buf
    margin_left = margin_left_buf
    margin_right = width - margin_right_buf

    return {
        "top": margin_top,
        "bottom": margin_bottom,
        "left": margin_left,
        "right": margin_right,
    }


# Analizza justowania
def analyze_line_alignment(
    line: TextLine, page_width: float, margins: Dict[str, float], tolerance: float = 5.0
) -> tuple:
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
            gap = line.spans[i + 1].bbox[0] - line.spans[i].bbox[2]
            if gap > 0:
                gaps.append(gap)

    is_consistent = True
    if len(gaps) > 1:
        # Sprawdzemie justowania poprzez odchylenie standardowe
        std_dev = statistics.stdev(gaps)
        if std_dev > 1.0:  # próg czułości
            is_consistent = False

    # Logika rozpoznawania stylu
    if is_at_left and is_at_right and not is_consistent:
        return (
            "justified",
            False,
            dist_right,
        )  # justowanie niepełne (błędne bo nierówne odstępy)
    elif is_at_left and is_at_right:
        return "justified", True, dist_right  # justowanie pełne
    elif abs(dist_left - dist_right) <= tolerance:
        return "center", True, dist_right  # tekst wyśrodkowany
    elif is_at_right:
        return "right", True, dist_right  # tekst wyrównany do prawej
    else:
        return "left", True, dist_right  # tekst wyrównany do lewej


def check_page_format(width, height, tolerance: float = 10) -> str:

    if height < width:
        orientation = "pozioma"
    else:
        orientation = "pionowa"

    formats = {"A5": (420, 595), "A4": (595, 842), "A3": (842, 1191)}

    for name, (w, h) in formats.items():
        for name, (w, h) in formats.items():
            if (abs(width - w) <= tolerance and abs(height - h) <= tolerance) or (
                abs(width - h) <= tolerance and abs(height - w) <= tolerance
            ):
                return name, orientation

    return "incorrect", orientation


def line_spacing(curr_line: float, prev_line: float, font_size: float) -> float | None:
    if prev_line is not None:
        return round(
            (curr_line - prev_line) / font_size / 1.2, 2
        )  # Z jakiegoś powodu trzeba przeskalować do 1.2 ??
    else:
        return None


def is_footer(raw_block: dict, page_height: float, page_num: int) -> bool:
    bbox = raw_block["bbox"]

    if bbox[1] < (page_height) * 0.88:
        return False

    text_content = ""
    for line in raw_block.get("lines", []):
        for span in line.get("spans", []):
            text_content += span.get("text", "")

    clean_text = text_content.lower().strip()
    patterns = [
        r"^\d+$",
        r"strona\s+\d+",  # strona x
        r"str\.\s*\d+",  # str. x
        r"^\d+\s*/\s*\d+$",  # "X / y
        r"^\d+\s+z\s+\d+$",  # x z y
        r"page\s+\d+",  # page x
        rf".*?\b{page_num}\b.*?",
    ]

    for p in patterns:
        if re.search(p, clean_text):
            return True

    return False


