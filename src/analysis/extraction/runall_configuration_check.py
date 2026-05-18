import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.extraction.extraction_json import extractPDF
from src.analysis.modules.redaction.redaction_validator import RedactionValidator
from src.analysis.extraction.converter_linguistics_clean import PDFMapper

# tu paths nie zmieniam bo to nie do exe tylko do testowania
def main():
    pdf_path = PROJECT_ROOT / "data" / "jago.pdf"

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

        validator = RedactionValidator(doc_data, doc_data_linguistics)
        found_errors = validator.validate()

        if not found_errors:
            print("Nie znaleziono błędów z redakcją")
        else:
            print(f"Znaleziono {len(found_errors)} błędów:")
            for error in found_errors:
                print(f"[{error.id}] Typ: {error.category}, Strona: {error.page_number}, Bbox: {error.bounding_box}, Text: {error.text}")
                print(f"  -> Komentarz: {error.comments}")
                print("-" * 40)

    except Exception as e:
        print(f"Wystąpił błąd podczas procesowania: {e}")

if __name__ == "__main__":
    main()