import logging
from pathlib import Path


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

import sys

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.extraction.extraction_json import extractPDF
from src.analysis.extraction.configuration_check import Configuration, Validator
from src.analysis.modules.redaction.redaction_validator import RedactionValidator
from src.analysis.extraction.converter_linguistics import PDFMapper

def main():
    #  Ścieżki do plików
    pdf_path = PROJECT_ROOT / "data" / "jago.pdf"
    config_path = PROJECT_ROOT / "src" / "config" / "wymagania_inz.json"

    if not Path(pdf_path).exists():
        print(f"Błąd: Nie znaleziono pliku PDF pod adresem: {pdf_path}")
        return

    try:
        config = Configuration(config_path)
        print("Konfiguracja załadowana pomyślnie.")

        print("Ekstrakcja danych z PDF... (to może chwilę potrwać)")
        doc_data = extractPDF(pdf_path)
        doc_data_linguistics = PDFMapper.map_to_schema(doc_data)
        
        validator = Validator(config)

        print("\n--- ROZPOCZĘCIE WALIDACJI ---")
        
        is_page_count_ok = validator.check_page_count(doc_data)
        is_font_size_ok = validator.check_font_size(doc_data)
        is_just_ok = validator.check_justification(doc_data)
        is_interline_ok = validator.check_interline_spacing(doc_data)
        is_format_ok = validator.check_format(doc_data)
        is_margins_ok = validator.check_margins(doc_data)
        is_orientation_ok = validator.check_orientation(doc_data)
        is_font_size_ok = validator.check_fonts(doc_data)


        if not validator.issues:
            print("\n Dokument jest zgodny z wybranymi parametrami konfiguracji!")
        else:
            print(f"\n Znaleziono błędy ({len(validator.issues)}):")
            for issue in validator.issues:
                page_info = f"strona {issue.page}" if issue.page > 0 else "cały dokument"
                print(f"  - [{issue.category}] ({page_info}): {issue.description}")

        validator = RedactionValidator(doc_data, doc_data_linguistics)
        found_errors = validator.validate()
    
        # Tymczasowe
        if not found_errors:
            print("Nie znaleziono błędów z redakcją")
        else:
            print(f"Znaleziono {len(found_errors)} błędów:")
            for error in found_errors:
                print(f"[{error.id}] Typ: {error.category}, Strona: {error.page_nr}, Bbox: {error.bounding_box}, Text: {error.text}")
                print(f"  -> Komentarz: {error.comments}")
                print("-" * 40)

    except Exception as e:
        print(f" Wystąpił błąd podczas procesowania: {e}")
        

if __name__ == "__main__":
    main()