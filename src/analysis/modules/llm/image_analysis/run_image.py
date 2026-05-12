import sys
import os
import json
import re
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))
sys.path.append(str(current_dir.parents[3])) 

import config 
from llava_engine import LlavaEngine
from reference_matcher import ReferenceMatcher
from consistency_checker import ConsistencyChecker

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
                            print(f"[Ostrzeżenie] Nie znaleziono pliku obrazka na dysku: {img_path}")
                    
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

def analyze_images(doc_obj, mapped_doc):
    llava = LlavaEngine()
    matcher = ReferenceMatcher()
    checker = ConsistencyChecker()

    paragraphs, images = adapt_data_for_images(doc_obj, mapped_doc)
    final_report = []

    for img in images:
        img_id = img["id"]
        image_bytes = img["bytes"]

        raw_refs = matcher.find_references(paragraphs, img_id)

        refs = []
        for r in raw_refs:
            if re.match(rf"(?i)^rys(?:unek|\.)?\s*{re.escape(str(img_id))}\s*[:\.\-]", r.strip()):
                continue 
            if len(r.strip()) < 50 and "rys" in r.lower():
                continue
            
            refs.append(r)

        if not refs:
            final_report.append({
                "obrazek": img_id,
                "odwolanie": "brak",
                "poprawnosc_danych": "False",
                "bledy": ["Brak prawdziwego odwołania omawiającego rysunek w tekście pracy (znaleziono jedynie podpis)."]
            })
            continue

        image_data = llava.extract_data(image_bytes)

        for ref_para in refs:
            verification = checker.check(ref_para, image_data)
            
            final_report.append({
                "obrazek": img_id,
                "odwolanie": "wystapilo",
                "poprawnosc_danych": verification.get("poprawnosc_danych", "False"),
                "bledy": verification.get("bledy", "None")
            })

    return final_report

if __name__ == "__main__":
    import config 
    print(f"Rozpoczynam testową analizę z konfiguracji: {config.THESIS_PATH}")
    
    from analysis.extraction.extraction_json import extractPDF
    from analysis.extraction.converter_linguistics_clean import PDFMapper
    
    doc_obj = extractPDF(str(config.THESIS_PATH))
    mapper = PDFMapper()
    mapped_doc = mapper.map_to_schema(doc_obj)
    
    wynik = analyze_images(doc_obj, mapped_doc)
    print(json.dumps(wynik, indent=4, ensure_ascii=False))