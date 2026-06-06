import sys
import os
import re
from pathlib import Path

# Wymuszenie kodowania UTF-8 dla terminala, aby uniknąć błędów Unicode przy symbolach matematycznych
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

current_dir = Path(__file__).resolve().parent

# Ścieżka do folderu 'llm' (żeby znalazł plik config.py!)
sys.path.append(str(current_dir.parent))
# Ścieżka do folderu 'src'
sys.path.append(str(current_dir.parents[3]))

import config 
from reference_matcher import ReferenceMatcher
def run_diagnostics(pdf_path):
    '''
    wejscie: pdf_path w formacie stringa (ścieżka do dokumentu PDF).
    wyjscie: brak (wypisuje statystyki i podsumowanie w konsoli).
    opis: Analizuje proces dopasowywania akapitów do obrazków i testuje skuteczność filtrów odrzucających zbędny tekst.
    '''
    print(f"Rozpoczynam zoptymalizowaną diagnostykę dla: {pdf_path}")
    
    from analysis.extraction.extraction_json import extractPDF
    from analysis.extraction.converter_linguistics_clean import PDFMapper
    
    # 1. Ekstrakcja i mapowanie lingwistyczne
    doc_obj = extractPDF(str(pdf_path))
    mapper = PDFMapper()
    mapped_doc = mapper.map_to_schema(doc_obj)
    
    # 2. Pobieranie akapitów (tak jak w run_image.py)
    paragraphs = []
    for block in mapped_doc.logical_blocks:
        text = getattr(block, "content", "").strip()
        if text:
            paragraphs.append(text)
            
    # 3. OPTYMALIZACJA: Deduplikacja obrazów przy użyciu słownika
    # Zapobiega to wielokrotnemu czytaniu tych samych warstw graficznych
    caption_pattern = re.compile(r"(?i)rys(?:unek|\.)?\s*(\d+(?:\.\d+)?)")
    unique_images = {} # Klucz: ID (np. "8.5"), Wartość: Pełny opis
    
    for page in doc_obj.pages:
        for img in page.images:
            desc = getattr(img, "description", "")
            if desc:
                match = caption_pattern.search(desc)
                if match:
                    found_id = match.group(1)
                    if found_id not in unique_images:
                        # Jeśli obrazka nie ma w słowniku, po prostu go dodajemy
                        unique_images[found_id] = {"desc": desc, "bytes": None}
                        # W run_image.py pobierz też bajty:
                        # img_path = Path(img.path)
                        # if img_path.exists():
                        #     with open(img_path, "rb") as f:
                        #         unique_images[found_id]["bytes"] = f.read()
                    else:
                        # Jeśli mamy duplikat (jak ten felerny 8.5), wybierzmy ten lepszy!
                        # Jeśli stary opis nie zaczyna się od "Rys", a nowy tak, nadpisz stary!
                        old_desc = unique_images[found_id]["desc"]
                        if not re.match(r"(?i)^rys", old_desc.strip()) and re.match(r"(?i)^rys", desc.strip()):
                             unique_images[found_id]["desc"] = desc
                             # Oraz nadpisz bajty nowym obrazkiem z dysku (w run_image.py)

    # --- DRUKOWANIE STATYSTYK ---
    print("\n" + "="*50)
    print("--- STATYSTYKI TEKSTU (AKAPITÓW) ---")
    print("="*50)
    print(f"Liczba bloków tekstu po mapowaniu: {len(paragraphs)}")
    if paragraphs:
        lengths = [len(p) for p in paragraphs]
        print(f"Najdłuższy akapit: {max(lengths)} znaków")
        print(f"Średnia długość: {sum(lengths)//len(lengths)} znaków")

    print("\n" + "="*50)
    print("--- STATYSTYKI OBRAZKÓW I FILTROWANIA ---")
    print("="*50)
    print(f"Liczba unikalnych obrazków (po deduplikacji): {len(unique_images)}")
    
    matcher = ReferenceMatcher()
    total_llm_calls = 0
    total_filtered_out = 0
    
    for img_id, img_desc in unique_images.items():
        # Znajdź wszystkie surowe dopasowania "Rys X.Y"
        raw_refs = matcher.find_references(paragraphs, img_id)
        
        # OPTYMALIZACJA: Filtrowanie podpisów (autoreferencji)
        # To jest logika przeniesiona bezpośrednio z poprawionego run_image.py
        filtered_refs = []
        for r in raw_refs:
            # Filtr 1: Czy to sam podpis zdjęcia? (zaczyna się od 'Rysunek ID')
            if re.match(rf"(?i)^rys(?:unek|\.)?\s*{re.escape(str(img_id))}\s*[:\.\-]", r.strip()):
                continue
            # Filtr 2: Czy to krótki fragment zawierający tylko 'rys'?
            if len(r.strip()) < 50 and "rys" in r.lower():
                continue
            
            filtered_refs.append(r)
        
        filtered_count = len(raw_refs) - len(filtered_refs)
        total_filtered_out += filtered_count
        total_llm_calls += len(filtered_refs)
        
        print(f"\n[Rysunek {img_id}]")
        print(f" -> Surowych odwołań: {len(raw_refs)}")
        print(f" -> Odrzuconych (podpisy/krótkie): {filtered_count}")
        print(f" -> Prawdziwych akapitów do analizy: {len(filtered_refs)}")
        
        for i, ref in enumerate(filtered_refs):
            snippet = ref.replace("\n", " ")[:120]
            print(f"    {i+1}. (Dł: {len(ref)}) {snippet}...")

    print("\n" + "="*50)
    print("--- PODSUMOWANIE ZYSKÓW ---")
    print("="*50)
    print(f"1. LLaVA (Obrazy) uruchomi się: {len(unique_images)} razy (Zredukowano z {sum(1 for p in doc_obj.pages for _ in p.images)})")
    print(f"2. Sędzia (Tekst) uruchomi się: {total_llm_calls} razy (Odrzucono {total_filtered_out} zbędnych wywołań)")
    print("="*50)
    
    # Realistyczne szacowanie czasu (RTX 4070 SUPER)
    # LLaVA: ~10s, Sędzia: ~25s (przy kontekście 4096 tokenów)
    est_seconds = (len(unique_images) * 10) + (total_llm_calls * 25)
    print(f"Przewidywany czas wykonania: ok. {est_seconds // 60} min {est_seconds % 60} sek.")

if __name__ == "__main__":
    run_diagnostics(config.THESIS_PATH)