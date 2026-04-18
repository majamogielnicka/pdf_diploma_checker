from pathlib import Path
import sys
import os

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)

from converter_linguistics import extractPDF, PDFMapper
from error_info import ErrorChecker

def main():
    input_pdf_path = PROJECT_ROOT / "data" / "zusz.pdf"
    output_error_json_path = PROJECT_ROOT / "src" / "analysis" / "extraction" / "error_check" / "output_error.json"
    

    print(f"Rozpoczynam przetwarzanie pliku: {input_pdf_path}")

    raw_doc = extractPDF(input_pdf_path)
    mapped_doc = PDFMapper.map_to_schema(raw_doc)
    print("Mapowanie struktury dokumentu zakończone.")

    print("Rozpoczynam analizę błędów (Linter)...")
    
    checker = ErrorChecker()
    checker.check_document(mapped_doc)
    
    checker.save_to_json(output_error_json_path)
    
    print(f"Analiza zakończona. Wyniki zapisano do: {output_error_json_path}")

if __name__ == "__main__":
    main()