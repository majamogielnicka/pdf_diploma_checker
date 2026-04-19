'''-----------------------przykład dla extraction_json.py-----------------------'''
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from extraction_json import extractPDF

input_path = PROJECT_ROOT / "data" / "doju2.pdf"
output_path = PROJECT_ROOT / "src" / "output.json"

# Tryb debugu:
# 0 - domyślny tryb, program działakorzystając z /thesis
# 1 - tryb debugowania, ułatwia pracę nad konkretną funkcjonalnością, korzysta z /redaction_debug
# TODO: dodać więcej przykładowych plików pdf do folderu /redaction_debug
# Format nazwy pdfa: <aspekt_do_sprawdzenia>_example.pdf
debug_mode = 0
debug_type = "0" # zmiana trybu debugowania (wpisać interesujący nas aspekt)
debug_path = str(PROJECT_ROOT / "src" / "analysis" / "extraction" / "redaction_debug" / "{debug_type}_example.pdf")

if debug_mode == 0:
    pdf_path = Path(input_path)
elif debug_mode == 1:
    candidate = Path(debug_path.format(debug_type=debug_type))
    if candidate.exists():
        pdf_path = candidate
    else:
        print(f"[extraction_json] Debug PDF not found: {candidate}. Falling back to default thesis path.")
        pdf_path = Path(input_path)

doc_data = extractPDF(str(pdf_path))

#TODO: dodac warunek sprqwdzjaacy blad do testow
if doc_data is not None:
    doc_data.to_json(output_path) 
    print("[extraction_json] JSON wygenerowany")
else:
    print(f"[extraction_json] Nie wygenerowano pliku JSON") 


# -----------------------przykład dla converter_linguistics.py-----------------------
from converter_linguistics import PDFMapper

output_path_linguistics = PROJECT_ROOT / "src" / "output_linguistics.json"
doc_data_linguistics = doc_data # Domyślnie mapowany jest plik wygenerowany przez extraction_json.py

# Odkomentować ponizej w celu osobnego potraktowania extraction_json i converter_linguistics
'''
input_path_linguistics = PROJECT_ROOT / "data" / "zusz.pdf"

debug_mode_linguistics = 1
debug_type_linguistics = "table" # zmiana trybu debugowania (wpisać interesujący nas aspekt)
debug_path_linguistics = str(PROJECT_ROOT / "src" / "analysis" / "extraction" / "redaction_debug" / "{debug_type}_example.pdf")

if debug_mode_linguistics == 0:
    pdf_path_linguistics = Path(input_path_linguistics)
elif debug_mode_linguistics == 1:
    candidate_linguistics = Path(debug_path_linguistics.format(debug_type_linguistics=debug_type_linguistics))
    if candidate_linguistics.exists():
        pdf_path_linguistics = candidate
    else:
        print(f"[converter_linguistics] Debug PDF not found: {candidate_linguistics}. Falling back to default thesis path.")
        pdf_path_linguistics = Path(input_path)

doc_data_linguistics = extractPDF(str(pdf_path_linguistics))
'''

if doc_data_linguistics is not None:
    final_doc = PDFMapper.map_to_schema(doc_data)
    final_doc.to_json(output_path_linguistics)
    print("[converter_linguistics] JSON wygenerowany")
else:
    print(f"[converter_linguistics] Nie wygenerowano pliku JSON") 