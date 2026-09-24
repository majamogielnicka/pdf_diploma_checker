"""
Tutaj znajdują się funkcje odpowiedzialne za ekstrakcję danych z PDF do jsona (surprise, surprise).
W przyszłości proponuje to przenieść jako metody struktury zamiast oddzielnych funkcji do wszystkiego
"""

import os
import fitz  # PyMuPDF
import statistics

from analysis.extraction.raw_extraction.bare_struct import (
    DocumentData,
    PageData,
)

from analysis.extraction.raw_extraction.geometry import (
    calculate_margins,
    check_page_format,
    is_footer,
)

from analysis.extraction.raw_extraction.image_extractor import (
    extract_raster_images,
    extract_vector_graphics,

)

from analysis.extraction.raw_extraction.table_extractor import (
    extract_apa_tables,
    extract_lineless_tables,
    extract_tables,
)

from analysis.extraction.raw_extraction.text_extractor import (parse_text_block)
from analysis.extraction.raw_extraction.front_and_back_matter import (
    extract_TOC, 
    extract_TOF, 
    extract_TOT
)


# from pdf_diploma_checker.src.analysis.extraction.bare_struct import DocumentData, PageData, TextBlock, TextLine, TextSpan, ImageInfo, TableInfo, TocData, TocEntry, TofData, TofEntry, TotData, TotEntry
# from src.analysis.extraction.bare_struct import DocumentData, PageData, TextBlock, TextLine, TextSpan, ImageInfo, TableInfo, TocData, TocEntry, TofData, TofEntry, TotData, TotEntry


# TODO: dodać więcej przykładowych plików pdf do folderu /redaction_debug
# Format nazwy pdfa: <aspekt_do_sprawdzenia>_example.pdf

# uzywam dekoratora dataclass bo:
# ma fajne automatyczne funkcje jak tworzenie __init__ automatycznie
# jest duzo bardziej czytelny (#team_c++)
# ma wbudowana funkcje asdict() (potem sie przyda do jsona)


def extractPDF(file_path: str) -> DocumentData:
    current_span_id = 0
    if not os.path.exists(file_path):
        # TODO:tutaj jakis wyjatek
        print("plik nie istnieje")
        return

    # sprawdzenie czy mamy folder "images", jeśli nie to tworzymy taki
    os.makedirs("images", exist_ok=True)

    # usuwanie obrazów z poprzedniego sprawdzania, żeby nie było chaosu
    for filename in os.listdir("images"):
        file_to_delete = os.path.join("images", filename)
        try:
            if os.path.isfile(file_to_delete):
                os.remove(file_to_delete)
        except Exception as e:
            print(f"Nie udało się usunąć starego pliku {file_to_delete}: {e}")

    # TODO: dalsza walidacja
    doc = fitz.open(file_path)
    metadata = doc.metadata
    document_data = DocumentData(metadata=metadata)

    # Priorytet dla wykrywania tabel i obrazów na górze lub dole (z reguły jest to stałe dla pracy)
    detected_priority = None
    detected_img_priority = "below"
    # Do wykrycia interlinii
    all_spacings = []

    for page_index, page in enumerate(doc):
        raw_dict = page.get_text("dict")
        word_list = page.get_text("words")
        p_width = page.rect.width
        p_height = page.rect.height

        page_format, page_orientation = check_page_format(p_width, p_height)

        blank_page = True

        cur_page = PageData(
            number=page_index,  # + 1 zostało usunięte, jako że strona tytułowa nie powinna być wliczana do numeracji
            width=p_width,
            height=p_height,
            margins=calculate_margins(raw_dict["blocks"], p_width, p_height),
            text_blocks=[],
            images=[],
            orientation=page_orientation,
            format=page_format,
            is_blank=True,
        )

        drawings = page.get_drawings()

        # table_bboxes = extract_tables(page, drawings, cur_page)
        last_block_btmline = None  # Ostatnia linia w bloku - do interlinii
        # Najpierw wyciągamy wszystkie bloki tekstowe ze strony
        for block in raw_dict["blocks"]:
            # typ 0 to tekst, typ 1 to obraz
            if block["type"] == 0:
                is_ftr = is_footer(block, p_height, page_index + 1)
                text_block, last_block_btmline, current_span_id = parse_text_block(
                    block,
                    word_list,
                    p_width,
                    cur_page.margins,
                    last_block_btmline,
                    current_span_id,
                    all_spacings,
                    is_ftr,
                )

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
            priority_side=detected_img_priority,
        )

        if all_spacings:  # Znajdywanie średniej interlinii wykorzystywanej w pliku
            for s in range(len(all_spacings)):
                all_spacings[s] = round(all_spacings[s], 1)
            mode = statistics.mode(all_spacings)
            document_data.metadata["avarge_line_spacing"] = mode

        table_bboxes, detected_priority = extract_tables(
            page, drawings, cur_page, detected_priority
        )

        apa_bboxes, detected_priority = extract_apa_tables(
            page, drawings, cur_page, table_bboxes, detected_priority
        )

        existing_for_lineless = table_bboxes + apa_bboxes
        lineless_bboxes, detected_priority = extract_lineless_tables(
            page, cur_page, existing_for_lineless, detected_priority
        )

        all_table_bboxes = table_bboxes + apa_bboxes + lineless_bboxes
        if all_table_bboxes:
            blank_page = False
        detected_img_priority = extract_vector_graphics(
            page,
            drawings,
            page_index,
            all_table_bboxes,
            cur_page,
            detected_img_priority,
        )
        if len(cur_page.images) > 0:
            blank_page = False
        cur_page.is_blank = blank_page
        document_data.pages.append(cur_page)
    document_data.toc = extract_TOC(doc, document_data.pages)
    document_data.tof = extract_TOF(
        document_data.pages, document_data.toc.page_nums if document_data.toc else []
    )
    document_data.tot = extract_TOT(
        document_data.pages, document_data.toc.page_nums if document_data.toc else []
    )
    doc.close()
    return document_data

