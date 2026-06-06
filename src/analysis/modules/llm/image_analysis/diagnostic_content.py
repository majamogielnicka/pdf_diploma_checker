import sys
import re
from pathlib import Path

# Wymuszenie kodowania UTF-8 dla terminala Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Poprawne ścieżki
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))      # Ścieżka do 'llm' (dla config.py)
sys.path.append(str(current_dir.parents[3]))  # Ścieżka do 'src'

import config 
from reference_matcher import ReferenceMatcher

def dump_diagnostics_to_file(pdf_path, output_filename="wynik_teksty.txt"):
    '''
    wejscie: pdf_path i opcjonalny output_filename w formacie stringów (ścieżki do plików).
    wyjscie: brak (zapisuje plik tekstowy na dysku).
    opis: Przeprowadza ekstrakcję tekstu z PDF i zrzuca do pliku akapity oraz odwołania do rysunków w celach diagnostycznych.
    '''
    print(f"Rozpoczynam zrzucanie tekstów dla pliku: {pdf_path}")
    print(f"Trwa ekstrakcja... To może chwilę potrwać.")
    
    from analysis.extraction.extraction_json import extractPDF
    from analysis.extraction.converter_linguistics_clean import PDFMapper
    
    # 1. Ekstrakcja
    doc_obj = extractPDF(str(pdf_path))
    mapper = PDFMapper()
    mapped_doc = mapper.map_to_schema(doc_obj)
    
    # 2. Pobieranie bazy akapitów
    paragraphs = []
    for block in mapped_doc.logical_blocks:
        text = getattr(block, "content", "").strip()
        if text:
            paragraphs.append(text)
            
    # 3. Pobieranie obrazków (Z NASZĄ NOWĄ MĄDRĄ DEDUPLIKACJĄ)
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
                        # Zapisujemy jako słownik!
                        unique_images[found_id] = {"desc": desc}
                    else:
                        # Nadpisujemy, jeśli znaleźliśmy lepszy podpis
                        old_desc = unique_images[found_id]["desc"]
                        if not re.match(r"(?i)^rys", old_desc.strip()) and re.match(r"(?i)^rys", desc.strip()):
                             unique_images[found_id]["desc"] = desc

    matcher = ReferenceMatcher()

    # Otwieramy plik z twardym wymuszeniem zapisu w UTF-8
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("==================================================\n")
        f.write("RAPORT DIAGNOSTYCZNY: ZAWARTOŚĆ TEKSTOWA\n")
        f.write("==================================================\n\n")

        f.write("--- 1. WYKRYTE RYSUNKI (Zdeduplikowane) ---\n")
        # ZMIANA TUTAJ: Zamiast 'desc' odbieramy całą 'datę' i wyciągamy z niej 'desc'
        for img_id, data in unique_images.items():
            desc_text = data["desc"]
            clean_desc = desc_text.replace("\n", " ") 
            f.write(f"[ID: {img_id}] Podpis: {clean_desc}\n")

        f.write("\n\n==================================================\n")
        f.write("--- 2. TEKSTY WYSYŁANE DO MODELU LLM (Dla każdego obrazka) ---\n")
        f.write("Tutaj widać pełne akapity, które Sędzia analizuje pod kątem spójności.\n")
        f.write("==================================================\n")

        # ZMIANA TUTAJ: Odbieramy 'data'
        for img_id, data in unique_images.items():
            raw_refs = matcher.find_references(paragraphs, img_id)
            
            filtered_refs = []
            for r in raw_refs:
                if re.match(rf"(?i)^rys(?:unek|\.)?\s*{re.escape(str(img_id))}\s*[:\.\-]", r.strip()):
                    continue
                if len(r.strip()) < 50 and "rys" in r.lower():
                    continue
                filtered_refs.append(r)

            f.write(f"\n\n---> RYSUNEK {img_id} <---\n")
            if not filtered_refs:
                f.write("Brak prawdziwych odwołań w tekście (LLM nie sprawdzi tego obrazka).\n")
            else:
                for i, ref in enumerate(filtered_refs):
                    f.write(f"\n[Akapit nr {i+1} | Długość: {len(ref)} znaków]:\n")
                    f.write(f"{ref}\n")
                    f.write("-" * 50 + "\n")

        f.write("\n\n==================================================\n")
        f.write("--- 3. SUROWA BAZA AKAPITÓW (Cały tekst odzyskiwany z PDF) ---\n")
        f.write("Sprawdź, czy moduł lingwistyczny nie ucina w pół słowa, albo czy łączy akapity prawidłowo.\n")
        f.write("==================================================\n\n")
        
        for i, para in enumerate(paragraphs):
            f.write(f"[Blok {i+1}]: {para}\n\n")

    print(f"\n✅ ZAKOŃCZONO! Cały raport został bezpiecznie zapisany w pliku: {output_filename}")
    print("Możesz go teraz otworzyć w Notatniku lub VSC i dokładnie przeanalizować.")

if __name__ == "__main__":
    # Plik zapisze się w głównym folderze projektu (tam gdzie uruchamiasz komendę)
    dump_diagnostics_to_file(config.THESIS_PATH, output_filename="wynik_teksty.txt")