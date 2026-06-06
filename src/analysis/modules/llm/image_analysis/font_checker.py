import sys
import os
import json
import re
import gc
import base64
from pathlib import Path
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))
sys.path.append(str(current_dir.parents[3]))

import config 

def extract_images_for_fonts(doc_obj, mapped_doc):
    """Extract real figure images and captions, filtering out text-only references."""
    caption_pattern = re.compile(r"(?:^|\n)\s*rys(?:unek|\.)?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
    unique_images = {}
    
    for page in doc_obj.pages:
        for img in getattr(page, "images", []):
            desc = getattr(img, "description", "").strip()
            if desc:
                match = caption_pattern.search(desc)
                if match:
                    found_id = match.group(1)
                    
                    if found_id not in unique_images:
                        unique_images[found_id] = {"desc": desc, "bytes": None}
                        img_path = Path(getattr(img, "path", ""))
                        if img_path.exists():
                            with open(img_path, "rb") as f:
                                unique_images[found_id]["bytes"] = f.read()
                    else:
                        old_desc = unique_images[found_id]["desc"]
                        if not re.match(r"(?i)^rys", old_desc.strip()) and re.match(r"(?i)^rys", desc.strip()):
                            unique_images[found_id]["desc"] = desc
                            img_path = Path(getattr(img, "path", ""))
                            if img_path.exists():
                                with open(img_path, "rb") as f:
                                    unique_images[found_id]["bytes"] = f.read()
                        
    images = [{"id": img_id, "bytes": data["bytes"]} for img_id, data in unique_images.items() if data["bytes"] is not None]
    return images

class LlavaFontEngine:
    """LLaVA-based engine for single-image font consistency checks."""
    def __init__(self, model_path=str(config.LLAVA_MODEL_PATH), mmproj_path=str(config.LLAVA_MMPROJ_PATH)):
        self.chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
        self.llm = Llama(
            model_path=model_path,
            chat_handler=self.chat_handler,
            n_ctx=4096,
            n_gpu_layers=config.N_GPU_LAYERS,
            logits_all=True,
            verbose=False 
        )

    def check_font_consistency(self, image_bytes):
        """Return whether font sizes in an image appear visually consistent."""
        base64_img = base64.b64encode(image_bytes).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{base64_img}"

        prompt = """Analyze the text and labels inside this single chart/image. 
        Are the font sizes consistent? (For example, all axis labels should be roughly the same size, with no randomly huge or tiny texts mixed together). 
        If the fonts are consistent and look uniform, answer ONLY with the word: YES.
        If the fonts are inconsistent or have mismatched sizes, answer ONLY with the word: NO.
        Do not explain. Do not use any other words."""

        try:
            response = self.llm.create_chat_completion(
                messages=[{
                    "role": "user", 
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}}, 
                        {"type": "text", "text": prompt}
                    ]
                }],
                temperature=0.0,
                max_tokens=10 
            )
            
            result_text = response["choices"][0]["message"]["content"].strip().lower()
            
            if "yes" in result_text or "true" in result_text:
                return {"consistent": True, "reason": "OK"}
            elif "no" in result_text or "false" in result_text:
                return {"consistent": False, "reason": "Model LLaVA wykrył niespójne rozmiary czcionek na obrazku."}
            else:
                return {"consistent": True, "reason": f"Niejednoznaczna odpowiedź AI: {result_text}. Domyślnie zaakceptowano."}
                
        except Exception as e:
            return {"consistent": False, "reason": f"Błąd przetwarzania AI: {str(e)}"}

def get_font_consistency_report(doc_obj, mapped_doc, verbose=False):
    """Return a report of figures with inconsistent font sizing."""
    images = extract_images_for_fonts(doc_obj, mapped_doc)
    bad_fonts_report = []

    if not images:
        return bad_fonts_report

    if verbose: print(f"\n[AI] Ładowanie modelu wizyjnego LLaVA (Spójność Czcionek) do VRAM...")
    
    llava = LlavaFontEngine()
    
    for idx, img in enumerate(images, 1):
        if verbose: print(f"[{idx}/{len(images)}] LLaVA weryfikuje czcionki Rysunku {img['id']}...")
        
        assessment = llava.check_font_consistency(img["bytes"])
        
        is_consistent = assessment.get("consistent", True)
        if str(is_consistent).lower() == "false":
            bad_fonts_report.append({
                "rysunek": f"Rys. {img['id']}",
                "blad": "Niespójne wielkości czcionek na wykresie/obrazku.",
                "szczegoly_ai": assessment.get("reason", "Model AI zauważył drastyczne różnice w wielkościach tekstu.")
            })
            
    if verbose: print(f"[AI] Zwalniam VRAM po analizie czcionek...")
    del llava
    gc.collect()
    
    return bad_fonts_report

if __name__ == "__main__":
    import time
    from config import THESIS_PATH
    from analysis.extraction.extraction_json import extractPDF
    from analysis.extraction.converter_linguistics_clean import PDFMapper
    
    print("MODUŁ: SPÓJNOŚĆ CZCIONEK NA OBRAZKACH")
    
    start_time = time.time()
    
    doc_obj = extractPDF(str(THESIS_PATH))
    mapped_doc = PDFMapper().map_to_schema(doc_obj)
    
    raport_czcionek = get_font_consistency_report(doc_obj, mapped_doc, verbose=True)
    
    end_time = time.time()
    print(f"CZAS WYKONANIA: {int(end_time - start_time)} sek.")
    print("--- RAPORT NIESPÓJNYCH CZCIONEK ---")
    if not raport_czcionek:
        print(json.dumps({"status": "Wszystkie obrazki mają piękne i spójne czcionki!"}, indent=4, ensure_ascii=False))
    else:
        print(json.dumps(raport_czcionek, indent=4, ensure_ascii=False))