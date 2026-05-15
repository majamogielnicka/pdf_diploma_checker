import sys
import os
import json
import re
import gc
from pathlib import Path

from analysis.modules.llm import config 
from analysis.modules.llm.image_analysis.llava_engine import LlavaEngine
from analysis.modules.llm.image_analysis.reference_matcher import ReferenceMatcher
from analysis.modules.llm.image_analysis.consistency_checker import ConsistencyChecker

def adapt_data_for_images(doc_obj, mapped_doc):
    """
    Adapter pobierający gotowe dane z głównej ekstrakcji PDF.
    - Z mapped_doc pobiera czyste akapity tekstu.
    - Z doc_obj pobiera zdeduplikowane obrazki i ich podpisy.
    """
    paragraphs = []
    
    for block in mapped_doc.logical_blocks:
        text = getattr(block, "content", "").strip()
        if text:
            paragraphs.append(text)
            
    caption_pattern = re.compile(r"(?i)rys(?:unek|\.)?\s*(\d+(?:\.\d+)?)")
    unique_images = {}
    
    for page in doc_obj.pages:
        for img in page.images:
            desc = getattr(img, "description", "")
            if desc:
                match = caption_pattern.search(desc)
                if match:
                    found_id = match.group(1)
                    
                    if found_id not in unique_images:
                        unique_images[found_id] = {"desc": desc, "bytes": None}
                        img_path = Path(img.path)
                        if img_path.exists():
                            with open(img_path, "rb") as f:
                                unique_images[found_id]["bytes"] = f.read()
                    else:
                        old_desc = unique_images[found_id]["desc"]
                        if not re.match(r"(?i)^rys", old_desc.strip()) and re.match(r"(?i)^rys", desc.strip()):
                            unique_images[found_id]["desc"] = desc
                            img_path = Path(img.path)
                            if img_path.exists():
                                with open(img_path, "rb") as f:
                                    unique_images[found_id]["bytes"] = f.read()
                        
    images = [{"id": img_id, "bytes": data["bytes"]} for img_id, data in unique_images.items() if data["bytes"] is not None]
    
    return paragraphs, images

def analyze_images(doc_obj, mapped_doc, verbose=False):
    """
    Analizuje obrazki i odwołania do nich.
    Jeśli verbose=False (domyślnie), funkcja nie wypisuje nic do terminala.
    """
    matcher = ReferenceMatcher()
    paragraphs, images = adapt_data_for_images(doc_obj, mapped_doc)
    
    images_with_refs = []
    final_report = []

    for img in images:
        raw_refs = matcher.find_references(paragraphs, img["id"])
        refs = []
        for r in raw_refs:
            if re.match(rf"(?i)^rys(?:unek|\.)?\s*{re.escape(str(img['id']))}\s*[:\.\-]", r.strip()):
                continue
            if len(r.strip()) < 50 and "rys" in r.lower():
                continue
            refs.append(r)

        if not refs:
            final_report.append({
                "obrazek": img["id"],
                "odwolanie": "brak",
                "poprawnosc_danych": "False",
                "bledy": ["Brak prawdziwego odwołania omawiającego rysunek w tekście pracy (znaleziono jedynie podpis)."]
            })
        else:
            images_with_refs.append({"id": img["id"], "bytes": img["bytes"], "refs": refs})

    if not images_with_refs:
        return final_report

    if verbose:
        print(f"\n[AI] Ładowanie modelu wizyjnego LLaVA do VRAM...")
        
    llava = LlavaEngine()
    extracted_image_data = {}
    
    for idx, img in enumerate(images_with_refs, 1):
        if verbose:
            print(f"[{idx}/{len(images_with_refs)}] LLaVA analizuje obrazek {img['id']}...")
        extracted_image_data[img["id"]] = llava.extract_data(img["bytes"])
  
    if verbose:
        print(f"\n[AI] Koniec pracy LLaVA. Zwalniam VRAM karty graficznej...")
        
    del llava
    gc.collect() 

    if verbose:
        print(f"\n[AI] Ładowanie Sędziego (Gemma) do VRAM...")
        
    checker = ConsistencyChecker()
    
    for img in images_with_refs:
        img_data_text = extracted_image_data[img["id"]]
        for ref_para in img["refs"]:
            if verbose:
                print(f" -> Sędzia ocenia akapit dla rysunku {img['id']}...")
                
            verification = checker.check(ref_para, img_data_text)
            
            final_report.append({
                "obrazek": img["id"],
                "odwolanie": "wystapilo",
                "poprawnosc_danych": verification.get("poprawnosc_danych", "False"),
                "bledy": verification.get("bledy", "None")
            })

    return final_report

if __name__ == "__main__":
    import time
    
    print("==================================================")
    print("URUCHAMIANIE TESTOWE ZOPTYMALIZOWANEGO RUN_IMAGE")
    print("==================================================")
    print(f"Plik: {config.THESIS_PATH}")
    
    from analysis.extraction.extraction_json import extractPDF
    from analysis.extraction.converter_linguistics_clean import PDFMapper
    
    start_time = time.time()
    
    print("\n[1/3] Trwa główna ekstrakcja z pliku PDF...")
    doc_obj = extractPDF(str(config.THESIS_PATH))
    print("[2/3] Trwa mapowanie lingwistyczne...")
    mapped_doc = PDFMapper().map_to_schema(doc_obj)
    
    print("\n[3/3] Rozpoczynamy analizę obrazów (AI)...")
    
    # Tutaj włączamy verbose=True, aby widzieć logi tylko podczas testów
    raport = analyze_images(doc_obj, mapped_doc, verbose=True)
    
    end_time = time.time()
    elapsed_time = int(end_time - start_time)
    
    print("\n==================================================")
    print("TEST ZAKOŃCZONY SUKCESEM!")
    print("==================================================")
    print(f"Czas wykonania: {elapsed_time // 60} min {elapsed_time % 60} sek.")
    
    print("\n--- RAPORT JSON ---")
    print(json.dumps(raport, indent=4, ensure_ascii=False))