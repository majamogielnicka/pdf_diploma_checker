import logging
from pathlib import Path
from extraction_json import extractPDF
from configuration_check import Configuration, Validator

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

import sys

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def main():
    #  Ścieżki do plików
    pdf_path = PROJECT_ROOT / "data" / "zusz.pdf"
    config_path = PROJECT_ROOT / "src" / "config" / "wymagania_inz.json"

    if not Path(pdf_path).exists():
        print(f"Błąd: Nie znaleziono pliku PDF pod adresem: {pdf_path}")
        return

    try:
        config = Configuration(config_path)
        print("Konfiguracja załadowana pomyślnie.")

        print("Ekstrakcja danych z PDF... (to może chwilę potrwać)")
        doc_data = extractPDF(pdf_path)
        
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

    except Exception as e:
        print(f" Wystąpił błąd podczas procesowania: {e}")

if __name__ == "__main__":
    main()