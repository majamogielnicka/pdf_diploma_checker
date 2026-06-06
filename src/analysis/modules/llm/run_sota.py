from dataclasses import dataclass
from find_sota import get_sota_chapter
from evaluate_sota import analyze_sota_chapter, free_sota_memory
from config import THESIS_PATH, LANGUAGE
import re

@dataclass
class ChapterBlock:
    id: int
    title: str
    content: str = ""

def is_toc_like(text):
    """
    Niszczarka Spisów Treści:
    Sprawdza, czy blok tekstu wygląda jak Spis Treści (TOC),
    szukając ciągów kropek kończących się numerem strony, np. "...... 34" lub ". . . 34"
    wejscie: text w formacie stringa.
    wyjscie: wartość logiczna (bool).
    opis: Weryfikuje za pomocą Regexów, czy przekazany tekst jest fragmentem spisu treści (TOC), aby pominąć go w analizie.
    """
    toc_lines = len(re.findall(r"(?:\.{3,}|\.\s\.\s\.)[\s\.]*\d+", text))
    return toc_lines >= 2

def adapt_extraction_to_blocks(mapped_doc):
    '''
    wejscie: mapped_doc (zmapowany dokument lingwistyczny z ekstraktora PDF).
    wyjscie: lista obiektów klasy ChapterBlock łączących tekst i nagłówki.
    opis: Agreguje luźne bloki tekstu w logicznie połączone rozdziały, odrzucając automatycznie m.in. spisy treści.
    '''     
    blocks = []
    current_title = "Początek"
    current_content = []
    block_id = 1
    
    for block in mapped_doc.logical_blocks:
        is_header = getattr(block, "type", "") == "heading"
        text = getattr(block, "content", "").strip()
        
        if not text:
            continue

        if is_header:
            is_main_chapter = bool(re.match(r"^\d+\.?\s+[A-ZĄĆĘŁŃÓŚŹŻ]", text.upper())) or text.upper() in ["WSTĘP", "PODSUMOWANIE", "ZAKOŃCZENIE", "BIBLIOGRAFIA", "LITERATURA"]
            
            if is_main_chapter:
                if current_content:
                    content_str = "\n".join(current_content)
                    if not is_toc_like(content_str):
                        blocks.append(ChapterBlock(
                            id=block_id, 
                            title=current_title, 
                            content=content_str
                        ))
                        block_id += 1
                
                clean_title = re.sub(r"\s+\d+$", "", text)
                current_title = clean_title
                current_content = [clean_title]
            else:
                current_content.append(text)
        else:
            current_content.append(text)

    if current_content:
        content_str = "\n".join(current_content)
        if not is_toc_like(content_str):
            blocks.append(ChapterBlock(
                id=block_id, 
                title=current_title, 
                content=content_str
            ))
    
    return blocks


def get_final_sota_report(mapped_doc, language: str = LANGUAGE):
    '''
    wejscie: mapped_doc (struktura dokumentu z PDF) oraz opcjonalny language (string).
    wyjscie: krotka zawierająca ostateczne dane raportu (id_rozdzialu, tytul, wynik_procentowy, metoda_wykrycia, ilosc_cytowan, R1, R2, R3).
    opis: Funkcja orkiestrująca, która zespaja cały pipeline SOTA – od odnalezienia rozdziału aż po jego ewaluację przez model LLM.
    '''
    
    sota_blocks = adapt_extraction_to_blocks(mapped_doc)

    s_id, s_title, s_method, s_citations, s_content = get_sota_chapter(sota_blocks, language)
    
    if s_id:
        print("\n--- DEBUG SOTA (CO WIDZI MODEL?) ---")
        print(f"Długość tekstu przekazanego do Gemmy: {len(s_content)} znaków")
        print(f"Początek tekstu:\n{s_content[:300]}...")
        print("------------------------------------\n")

    if not s_id:
        return None, None, 0, "Brak", 0, False, False, False

    try:
        ocena_data = analyze_sota_chapter(s_title, s_content)
        
        s_score = int(ocena_data["procent"])
        r1 = bool(ocena_data["r1"])
        r2 = bool(ocena_data["r2"])
        r3 = bool(ocena_data["r3"])
        
    except Exception as e:
        print(f"Błąd analizy SOTA: {e}")
        s_score = 0
        r1 = r2 = r3 = False
    finally:
        free_sota_memory()

    return s_id, s_title, s_score, s_method, s_citations, r1, r2, r3


if __name__ == "__main__":
    print(f"Rozpoczynam testową analizę z konfiguracji: {THESIS_PATH}")
    
    import sys
    import os
    import time 
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
        
    from analysis.extraction.extraction_json import extractPDF
    from analysis.extraction.converter_linguistics_clean import PDFMapper
    
    start_time = time.time()
    doc_data = extractPDF(str(THESIS_PATH))
    mapper = PDFMapper()
    mapped_data = mapper.map_to_schema(doc_data)

    res_id, res_title, res_score, res_method, res_cites, r1, r2, r3 = get_final_sota_report(mapped_data, LANGUAGE)
    end_time = time.time() 
    elapsed_time = int(end_time - start_time)

    print("\n" + "="*50)
    print(f"CZAS WYKONANIA: {elapsed_time // 60} min {elapsed_time % 60} sek.")
    print("="*50)

    print(f"\n--- WYNIKI ---")
    print(f"ID: {res_id}")
    print(f"Tytuł: {res_title}")
    print(f"Wynik: {res_score}%")
    print(f"Podstawa wyboru: {res_method}")
    print(f"R1: {r1}, R2: {r2}, R3: {r3}")