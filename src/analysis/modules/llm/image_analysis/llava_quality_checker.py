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

def extract_images_for_quality(doc_obj, mapped_doc):
    '''
    wejscie: doc_obj (obiekt PDF) oraz mapped_doc (zmapowana struktura dokumentu).
    wyjscie: lista słowników w formacie [{"id": str, "bytes": bytes}] przygotowana do oceny jakości.
    opis: Pobiera z dokumentu obrazki mające przypisaną numerację w celu weryfikacji ich czytelności.
    ''' 
    paragraphs = []
    for block in mapped_doc.logical_blocks:
        text = getattr(block, "content", "").strip()
        if text: 
            paragraphs.append(text)
            
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
                                    
    return [{"id": img_id, "bytes": data["bytes"]} for img_id, data in unique_images.items() if data["bytes"] is not None]

class LlavaQualityEngine:
    def __init__(self, model_path=str(config.LLAVA_MODEL_PATH), mmproj_path=str(config.LLAVA_MMPROJ_PATH)):
        '''
        wejscie: model_path i mmproj_path w formacie stringów (ścieżki do plików modelu).
        wyjscie: brak (inicjalizacja instancji klasy).
        opis: Uruchamia instancję modelu LLaVA przygotowaną do sprawdzania czytelności obrazów.
        '''
        self.chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
        self.llm = Llama(
            model_path=model_path, 
            chat_handler=self.chat_handler, 
            n_ctx=4096, 
            n_gpu_layers=-1, 
            logits_all=True, 
            verbose=False
        )

    def assess_quality(self, image_bytes):
        '''
        wejscie: image_bytes w formacie surowych bajtów obrazu.
        wyjscie: słownik w formacie dict z kluczami "czytelny" (bool) oraz "powod" (str).
        opis: Ocenia wizualnie za pomocą sztucznej inteligencji, czy dane na obrazku są rozmazane lub niewyraźne.
        '''
        base64_img = base64.b64encode(image_bytes).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{base64_img}"
        

        prompt = "Analyze the quality of this image. Is the text clear and readable? Is the image sharp? Answer ONLY 'YES' if it is good quality and readable. Answer ONLY 'NO' if it is blurry, pixelated, or unreadable. Do not explain."
        
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
                max_tokens=15 
            )
            
            result_text = response["choices"][0]["message"]["content"].strip().lower()
            
            if "yes" in result_text:
                return {"czytelny": True, "powod": "OK"}
            elif "no" in result_text:
                return {"czytelny": False, "powod": "Model LLaVA uznał, że obraz jest niewyraźny lub rozmazany."}
            else:
            
                return {"czytelny": True, "powod": "OK"}
                
        except Exception as e:
            return {"czytelny": False, "powod": f"Błąd weryfikacji wizualnej AI: {str(e)}"}

def get_llava_quality_report(doc_obj, mapped_doc, verbose=False):
    '''
    wejscie: doc_obj (obiekt PDF), mapped_doc (struktura dokumentu) i verbose (flaga logiczna).
    wyjscie: lista słowników reprezentujących znalezione błędy związane ze słabą czytelnością obrazków.
    opis: Przeprowadza pełną analizę czytelności wszystkich zidentyfikowanych wykresów i rysunków w pliku.
    '''
    images = extract_images_for_quality(doc_obj, mapped_doc)
    bad_images_report = []
    
    if not images: 
        return bad_images_report
        
    if verbose: 
        print("[AI] Ladowanie modelu do oceny wizualnej...")
        
    llava = LlavaQualityEngine()
    
    for img in images:
        if verbose: 
            print(f" -> LLaVA ocenia Rysunek {img['id']}...")
            
        assessment = llava.assess_quality(img["bytes"])
        czytelny = assessment.get("czytelny", True)
        
        if str(czytelny).lower() == "false":
            bad_images_report.append({
                "rysunek": f"Rys. {img['id']}", 
                "blad_llava": assessment.get("powod", "Obraz nieczytelny.")
            })
            
    if verbose: 
        print("[AI] Zwalnianie VRAM.")
        
    del llava
    gc.collect()
    
    return bad_images_report