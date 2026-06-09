import re
import os
import sys
import json
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise ImportError("Brak biblioteki Pillow. Uruchom: pip install Pillow")

try:
    import fitz
except ImportError:
    raise ImportError("Brak biblioteki PyMuPDF. Uruchom: pip install PyMuPDF")


def check_image_quality(doc_obj, pdf_path, dpi_threshold=75):
    low_quality_report = []
    
    caption_pattern = re.compile(r"(?:^|\n)\s*rys(?:unek|\.)?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
    
    unique_images = {}
    
    for page in doc_obj.pages:
        for img in getattr(page, "images", []):
            desc = getattr(img, "description", "").strip()
            if desc:
                match = caption_pattern.search(desc)
                if match:
                    found_id = match.group(1)
                    img_path = Path(getattr(img, "path", ""))
                    
                    if img_path.exists():
                        if found_id not in unique_images:
                            unique_images[found_id] = {"desc": desc, "path": img_path}
                        else:
                            old_desc = unique_images[found_id]["desc"]
                            if not re.match(r"(?i)^rys", old_desc.strip()) and re.match(r"(?i)^rys", desc.strip()):
                                unique_images[found_id] = {"desc": desc, "path": img_path}

    pdf_doc = fitz.open(str(pdf_path))
    dpi_map = {} 
    
    for page in pdf_doc:
        for img_info in page.get_image_info():
            bbox = img_info.get("bbox") 
            w_px = img_info.get("width", 0)
            h_px = img_info.get("height", 0)
            
            if bbox and w_px > 0 and h_px > 0:
                w_inches = (bbox[2] - bbox[0]) / 72.0 
                if w_inches > 0:
                    real_dpi = int(w_px / w_inches)
                    dpi_map[(w_px, h_px)] = real_dpi

    for img_id, data in unique_images.items():
        img_path = data["path"]
        extension = img_path.suffix.lower()
        
        if extension in ['.svg', '.eps', '.pdf']:
            continue 
            
        try:
            with Image.open(img_path) as image_file:
                w, h = image_file.size
                
                actual_dpi = dpi_map.get((w, h))
                
                if not actual_dpi:
                    file_dpi = image_file.info.get('dpi')
                    if file_dpi:
                        actual_dpi = int(file_dpi[0])
                        
                if not actual_dpi:
                    actual_dpi = int(w / 6.0)

                if actual_dpi < dpi_threshold:
                    low_quality_report.append({
                        "rysunek": f"Rys. {img_id}",
                        "format": extension.upper().replace(".", ""),
                        "rozdzielczosc_wewnetrzna": f"{w}x{h} px",
                        "zageszczenie_pikseli": f"~{actual_dpi} DPI",
                        "blad": "Obraz został nadmiernie rozciągnięty, co spowodowało widoczną 'pikselozę'.",
                        "wymaganie": f"Minimum {dpi_threshold} DPI (Standardowy zrzut ekranu ma 96 DPI)"
                    })
        except Exception as e:
            low_quality_report.append({
                "rysunek": f"Rys. {img_id}",
                "format": extension.upper().replace(".", ""),
                "rozdzielczosc_wewnetrzna": "Błąd odczytu",
                "blad": f"Nie udało się zweryfikować pliku: {e}",
                "wymaganie": "Zalecana wymiana grafiki."
            })
            
    low_quality_report.sort(key=lambda x: float(x["rysunek"].replace("Rys. ", "")))
    return low_quality_report


if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    llm_dir = os.path.abspath(os.path.join(current_dir, ".."))
    if llm_dir not in sys.path:
        sys.path.insert(0, llm_dir)
    src_dir = os.path.abspath(os.path.join(llm_dir, "..", "..", ".."))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        
    from analysis.modules.llm.config import THESIS_PATH
    from analysis.extraction.extraction_json import extractPDF
    
    print(f"Szukam pliku PDF pod ścieżką: {THESIS_PATH}")
    if not os.path.exists(str(THESIS_PATH)):
        print(f"BŁĄD KRYTYCZNY: Plik PDF nie istnieje! Upewnij się, że w config.py masz poprawną ścieżkę absolutną.")
        sys.exit(1)
        
    print("Rozpoczynam ekstrakcję PDF...")
    doc_obj = extractPDF(str(THESIS_PATH))
    
    if doc_obj is None:
        print("BŁĄD KRYTYCZNY: Funkcja 'extractPDF' zwróciła 'None'.")
        sys.exit(1)
    
    print("\nSprawdzanie zagęszczenia pikseli obrazów (Minimum 75 DPI)...")
    raport_jakosci = check_image_quality(doc_obj, str(THESIS_PATH), dpi_threshold=75)
    
    if not raport_jakosci:
        print("Wszystkie obrazy w pracy są idealnie ostre (powyżej wymaganego DPI lub wektory)!")
    else:
        print(f"Znaleziono {len(raport_jakosci)} obrazków o słabej ostrości:")
        print(json.dumps(raport_jakosci, indent=4, ensure_ascii=False))