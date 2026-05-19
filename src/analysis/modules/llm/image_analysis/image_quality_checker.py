import sys
import os
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))
sys.path.append(str(current_dir.parents[3]))

from .quality_analysis import check_image_quality
from .llava_quality_checker import get_llava_quality_report

def get_full_image_quality_json(doc_obj, mapped_doc, pdf_path, verbose=False):
    """
    Czysta funkcja do użycia w Twoim głównym pipeline.
    Zwraca ostateczny raport jako listę słowników (JSON).
    """
    if verbose: print("[1/2] Test matematyczny DPI (próg 75)...")
    dpi_report = check_image_quality(doc_obj, str(pdf_path), dpi_threshold=75)
    
    if verbose: print("[2/2] Test wizualny LLaVA (czytelność)...")
    llava_report = get_llava_quality_report(doc_obj, mapped_doc, verbose=verbose)
    
    merged_results = {}
    
    for item in dpi_report:
        rys = item["rysunek"]
        merged_results[rys] = {
            "rysunek": rys,
            "format": item.get("format", "Nieznany"),
            "powody_odrzucenia": [f"[DPI]: {item.get('blad')} (Wynik: {item.get('zageszczenie_pikseli')})"]
        }
        
    for item in llava_report:
        rys = item["rysunek"]
        blad_ai = f"[LLaVA AI]: {item.get('blad_llava')}"
        
        if rys in merged_results:

            merged_results[rys]["powody_odrzucenia"].append(blad_ai)
        else:
        
            merged_results[rys] = {
                "rysunek": rys,
                "format": "Wyciągnięto z PDF",
                "powody_odrzucenia": [blad_ai]
            }
            
    final_list = list(merged_results.values())
    
    try:
        final_list.sort(key=lambda x: float(x["rysunek"].replace("Rys. ", "")))
    except Exception:
        pass 
        
    return final_list

if __name__ == "__main__":
    
    import json
    from config import THESIS_PATH
    from analysis.extraction.extraction_json import extractPDF
    from analysis.extraction.converter_linguistics_clean import PDFMapper
    
    print("Rozpoczynam ekstrakcję do testu scalania...")
    doc_obj = extractPDF(str(THESIS_PATH))
    mapped_doc = PDFMapper().map_to_schema(doc_obj)
    
    final_report = get_full_image_quality_json(doc_obj, mapped_doc, THESIS_PATH, verbose=True)
    
    print("\n--- OSTATECZNY JSON DLA PIPELINE ---")
    print(json.dumps(final_report, indent=4, ensure_ascii=False))

# PRZYKŁADOWY OUTPUT GDY ZNAJDZIE BŁĄD, GDY NIE MA BLĘDÓW FUNKCJA ZWRACA PUSTĄ LISTE
#     [
#     {
#         "rysunek": "Rys. 1",
#         "format": "PNG",
#         "powody_odrzucenia": [
#             "[DPI]: Obraz został nadmiernie rozciągnięty, co spowodowało widoczną 'pikselozę'. (Wynik: ~42 DPI)"
#         ]
#     },
#     {
#         "rysunek": "Rys. 2.1",
#         "format": "Wyciągnięto z PDF",
#         "powody_odrzucenia": [
#             "[LLaVA AI]: Model LLaVA uznał, że obraz jest niewyraźny lub rozmazany."
#         ]
#     },
#     {
#         "rysunek": "Rys. 3",
#         "format": "JPG",
#         "powody_odrzucenia": [
#             "[DPI]: Obraz został nadmiernie rozciągnięty, co spowodowało widoczną 'pikselozę'. (Wynik: ~30 DPI)",
#             "[LLaVA AI]: Model LLaVA uznał, że obraz jest niewyraźny lub rozmazany."
#         ]
#     }
# ]