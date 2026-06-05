import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(PROJECT_ROOT)) 
sys.path.insert(0, str(SRC_DIR))  

from analysis.extraction.extraction_json import extractPDF
from analysis.modules.redaction.redaction_validator import RedactionValidator
from analysis.extraction.converter_linguistics_clean import PDFMapper

def main():

    pdf_path = PROJECT_ROOT / "data"  / "cyza.pdf"
    output_report_path = PROJECT_ROOT / "raport_bledow_redakcji.txt"

    possible_config_paths = [
        PROJECT_ROOT / "src" / "app" / "configuration.json",
        PROJECT_ROOT / "data" / "config"/ "wymagania_inz.json",
        PROJECT_ROOT / "configuration.json"
    ]
    
    config_path = None
    for p in possible_config_paths:
        if p.exists():
            config_path = p
            break

    if not Path(pdf_path).exists():
        print(f"Błąd: Nie znaleziono pliku PDF pod adresem: {pdf_path}")
        return

    try:
        print("Ekstrakcja danych z PDF... (to może chwilę potrwać)")
        doc_data = extractPDF(pdf_path)

        print("Mapowanie danych do schematu lingwistycznego...")
        mapper = PDFMapper()
        doc_data_linguistics = mapper.map_to_schema(doc_data)

        print("\n--- WALIDACJA REDAKCJI ---")

        if config_path:
            print(f"Ładowanie konfiguracji uczelnianej z: {config_path.name}")
            validator = RedactionValidator(doc_data, doc_data_linguistics, str(config_path))
        else:
            print("Ostrzeżenie: Nie znaleziono pliku configuration.json! Walidacja uruchomiona bez reguł formatowania.")
            validator = RedactionValidator(doc_data, doc_data_linguistics)
            
        found_errors = validator.validate()

        with open(output_report_path, "w", encoding="utf-8") as file:
            file.write("=== RAPORT BŁĘDÓW REDAKCJI ===\n")
            file.write(f"Plik źródłowy: {pdf_path.name}\n")
            if config_path:
                file.write(f"Użyta konfiguracja: {config_path.name}\n")
            file.write("-" * 50 + "\n\n")

            if not found_errors:
                file.write("Nie znaleziono błędów z redakcją.\n")
                print("Zakończono sukcesem! Nie znaleziono żadnych błędów z redakcją.")
            else:
                file.write(f"Znaleziono {len(found_errors)} błędów:\n\n")
                
                for error in found_errors:
                    file.write(f"[{error.id}] Typ: {error.category}\n")
                    file.write(f"     Strona: {error.page_number}\n")
                    file.write(f"     Bbox: {error.bounding_box}\n")
                    file.write(f"     Tekst: {error.text}\n")
                    file.write(f"     Komentarz: {error.comments}\n")
                    file.write("-" * 40 + "\n")
                
                print(f"Zakończono pomyślnie! Znaleziono {len(found_errors)} błędów.")
                print(f"Pełny raport tekstowy został wygenerowany w: {output_report_path}")

    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas procesowania: {e}")

if __name__ == "__main__":
    main()