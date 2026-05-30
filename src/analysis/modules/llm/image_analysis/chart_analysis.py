import sys
import os
import json
import gc
import base64
import re
from pathlib import Path
from llama_cpp import Llama, LlamaGrammar
from llama_cpp.llama_chat_format import Llava15ChatHandler

current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))
sys.path.append(str(current_dir.parents[3]))

import config

def extract_images(doc_obj):
    caption_pattern = re.compile(
        r"(?i)(rys(?:unek|\.)?|wykres|schemat|fot(?:ografia|\.)?|wys\.?)\s*(\d+(?:\.\d+)*)"
    )
    unique_images = {}
    idx = 1
    
    for page in doc_obj.pages:
        for img in getattr(page, "images", []):
            img_path = Path(getattr(img, "path", ""))
            if img_path.exists() and img_path not in unique_images:
                desc = getattr(img, "description", "").strip()
                match = caption_pattern.search(desc)
                
                if match:
                    prefix = match.group(1).capitalize()
                    
                    # Normalizacja przedrostków, aby JSON wyglądał spójnie i profesjonalnie
                    if prefix.startswith("Rys") and prefix != "Rysunek":
                        prefix = "Rys."
                    elif prefix.startswith("Wys"):
                        prefix = "Wys."
                    elif prefix.startswith("Fot") and prefix != "Fotografia":
                        prefix = "Fot."
                    else:
                        prefix = prefix.replace(".", "") # Usuwa kropki np. z pełnego słowa 'Wykres'
                        
                    label = f"{prefix} {match.group(2)}"
                else:
                    label = f"Obrazek {idx}" # Fallback dla obrazków bez widocznego podpisu
                
                with open(img_path, "rb") as f:
                    unique_images[img_path] = {
                        "bytes": f.read(),
                        "label": label
                    }
                idx += 1
                
    return [{"label": v["label"], "bytes": v["bytes"]} for v in unique_images.values()]

class LlavaChartEngine:
    def __init__(self, model_path=str(config.LLAVA_MODEL_PATH), mmproj_path=str(config.LLAVA_MMPROJ_PATH)):
        self.chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
        self.llm = Llama(
            model_path=model_path,
            chat_handler=self.chat_handler,
            n_ctx=4096,
            n_gpu_layers=-1,
            logits_all=True,
            verbose=False 
        )

    def analyze_chart(self, image_bytes):
        base64_img = base64.b64encode(image_bytes).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{base64_img}"

        prompt = """Look at this image. First, determine if it is an actual data chart/plot with X and Y axes. Then answer the following 6 questions:
        1. is_actual_chart_with_axes: Does this image clearly show a data chart with mathematical axes?
        2. embedded_title: Is there a main title printed INSIDE the chart graphic itself?
        3. has_axis_units: Do the axis labels contain units enclosed in square brackets?
        4. axis_ends_with_dot: Do the axis labels incorrectly end with a period/dot?
        5. has_axis_arrows: Are there arrows at the very ends of the standard X and Y axes lines?
        6. is_polish: Is the text inside the chart written in Polish?"""

        grammar_text = r'''
        root ::= "{" ws "\"is_actual_chart_with_axes\":" ws boolean "," ws "\"embedded_title\":" ws boolean "," ws "\"has_axis_units\":" ws boolean "," ws "\"axis_ends_with_dot\":" ws boolean "," ws "\"has_axis_arrows\":" ws boolean "," ws "\"is_polish\":" ws boolean "}"
        boolean ::= "true" | "false"
        ws ::= [ \t\n]*
        '''
        grammar = LlamaGrammar.from_string(grammar_text)

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
                max_tokens=100,
                grammar=grammar
            )
            return json.loads(response["choices"][0]["message"]["content"].strip())
        except Exception:
            return None

def get_chart_correctness_report(doc_obj):
    images = extract_images(doc_obj)
    bad_charts_report = []

    if not images:
        return json.dumps(bad_charts_report)

    llava = LlavaChartEngine()
    
    for img in images:
        analysis = llava.analyze_chart(img["bytes"])
        
        if analysis and analysis.get("is_actual_chart_with_axes") is True:
            bledy = []
            
            if analysis.get("embedded_title") is True:
                bledy.append("Wykres posiada tytuł wewnątrz obrazka.")
            if analysis.get("has_axis_units") is False:
                bledy.append("Brak jednostek w nawiasach kwadratowych na osiach wykresu.")
            if analysis.get("axis_ends_with_dot") is True:
                bledy.append("Opisy osi błędnie kończą się kropką.")
            if analysis.get("has_axis_arrows") is True:
                bledy.append("Oś X lub Y posiada strzałkę na końcu.")
            if analysis.get("is_polish") is False:
                bledy.append("Tekst na wykresie nie jest w języku polskim.")

            if bledy:
                bad_charts_report.append({
                    "rysunek": img["label"],
                    "bledy": bledy
                })
                
    del llava
    gc.collect()
    
    return json.dumps(bad_charts_report, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    from analysis.extraction.extraction_json import extractPDF
    
    doc_obj = extractPDF(str(config.THESIS_PATH))
    raport_json = get_chart_correctness_report(doc_obj)
    
    print(raport_json)
