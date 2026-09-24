"""
File can be used for debugging. By using this script you can 
generate list of redaction errors and document structure
of a document devided into pages and other sub-structures.
"""
import logging
import json
import sys
from pathlib import Path
from dataclasses import asdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from analysis.extraction.main_extractor import extractPDF
from analysis.extraction.linguistics_extraction.converter_linguistics_clean import PDFMapper
from src.analysis.modules.redaction.redaction_validator import RedactionValidator

def run_debugger(pdf_path, debug_mode=False, debug_type="toc"):
    
    if debug_mode:
        candidate = (
            PROJECT_ROOT / "src" / "analysis" / "extraction" / "redaction_debug" / f"{debug_type}_example.pdf"
        )
        if candidate.exists():
            pdf_path = candidate
        else:
            print(f"[DEBUG] Debug PDF not found: {candidate}. Using provided path: {pdf_path}")
    
    if not Path(pdf_path).exists():
        print(f"Błąd: Nie znaleziono pliku PDF: {pdf_path}")
        return

    # 1. Ekstrakcja
    print(f"[1/3] Ekstrakcja z: {Path(pdf_path).name}")
    doc_data = extractPDF(str(pdf_path))
    if doc_data is None:
        print("Błąd: Ekstrakcja nie powiodła się.")
        return
    
    # Zapis surowego JSON (opcjonalnie, z pierwszego skryptu)
    doc_data.to_json(PROJECT_ROOT / "src" / "output.json")
    print("JSON wygenerowany - w pliku output.json.")

    # 2. Mapowanie lingwistyczne
    print("[2/3] Mapowanie lingwistyczne")
    mapper = PDFMapper()
    doc_data_linguistics = mapper.map_to_schema(doc_data)
    
    if doc_data_linguistics:
        with open(PROJECT_ROOT / "src" / "output_linguistics.json", "w", encoding="utf-8") as f:
            json.dump(asdict(doc_data_linguistics), f, ensure_ascii=False, indent=4)
        print(f"JSON lingwistyczny wygenerowany w pliku output_linguistics.json.")
    else:
        print("Błąd: Mapowanie lingwistyczne nie powiodło się.")
        return

    # 3. Walidacja redakcji
    print("[3/3] Walidacja redakcji")
    possible_config_paths = [
        PROJECT_ROOT / "src" / "app" / "configuration.json",
        PROJECT_ROOT / "data" / "config" / "wymagania_inz.json",
        PROJECT_ROOT / "configuration.json",
    ]
    config_path = next((p for p in possible_config_paths if p.exists()), None)

    if config_path:
        print(f"Ładowanie konfiguracji: {config_path.name}")
        validator = RedactionValidator(doc_data, doc_data_linguistics, str(config_path))
    else:
        print("Ostrzeżenie: Brak konfiguracji! Walidacja bez reguł.")
        validator = RedactionValidator(doc_data, doc_data_linguistics)

    found_errors = validator.validate()
    
    # Raport
    output_report_path = PROJECT_ROOT / "raport_bledow_redakcji.txt"
    with open(output_report_path, "w", encoding="utf-8") as file:
        file.write("=== RAPORT BŁĘDÓW REDAKCJI ===\n")
        file.write(f"Plik źródłowy: {Path(pdf_path).name}\n")
        if config_path:
            file.write(f"Użyta konfiguracja: {config_path.name}\n")
        file.write("-" * 50 + "\n\n")

        if not found_errors:
            file.write("Nie znaleziono błędów z redakcją.\n")
            print("Zakończono sukcesem!")
        else:
            file.write(f"Znaleziono {len(found_errors)} błędów:\n\n")
            for error in found_errors:
                file.write(f"[{error.id}] Typ: {error.category}\n")
                file.write(f"     Strona: {error.page_number}\n")
                file.write(f"     Bbox: {error.bounding_box}\n")
                file.write(f"     Tekst: {error.text}\n")
                file.write(f"     Komentarz: {error.comments}\n")
                file.write("-" * 40 + "\n")
            print(f"Znaleziono {len(found_errors)} błędów. Raport w: {output_report_path}")

if __name__ == "__main__":
    input_pdf = PROJECT_ROOT / "data" / "prace" / "zusz.pdf"
    
    run_debugger(input_pdf, debug_mode=False, debug_type="toc")