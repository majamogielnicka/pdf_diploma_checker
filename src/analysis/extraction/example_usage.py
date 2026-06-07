'''-----------------------przykład dla extraction_json.py-----------------------'''
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]

SRC_DIR = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


from analysis.extraction.extraction_json import extractPDF

#input_path = PROJECT_ROOT / "data"  / "mock_data"/ "mock1.pdf"
input_path = PROJECT_ROOT / "data"  / "jabi.pdf"

output_path = PROJECT_ROOT / "src" / "output.json"

# Tryb debugu:
# 0 - domyślny tryb, program działakorzystając z /thesis
# 1 - tryb debugowania, ułatwia pracę nad konkretną funkcjonalnością, korzysta z /redaction_debug
# TODO: dodać więcej przykładowych plików pdf do folderu /redaction_debug
# Format nazwy pdfa: <aspekt_do_sprawdzenia>_example.pdf
debug_mode = 0
debug_type = "toc" # zmiana trybu debugowania (wpisać interesujący nas aspekt)

# ZAKOMENTOWANO: Stary zapis z metodą .format(), która słabo współpracuje z obiektami Path
# debug_path = str(PROJECT_ROOT / "src" / "analysis" / "extraction" / "redaction_debug" / "{debug_type}_example.pdf")

if debug_mode == 0:
    pdf_path = Path(input_path)
elif debug_mode == 1:
    # ZMIENIONO: Bezpieczne tworzenie ścieżki za pomocą f-stringa na poziomie Path
    candidate = PROJECT_ROOT / "src" / "analysis" / "extraction" / "redaction_debug" / f"{debug_type}_example.pdf"
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
from analysis.extraction.converter_linguistics_clean import PDFMapper, get_acronyms_lut
import json
from dataclasses import asdict

mapper = PDFMapper()

output_path_linguistics = PROJECT_ROOT / "src" / "output_linguistics.json"
mapped_doc = mapper.map_to_schema(doc_data)

if mapped_doc is not None:
    with open(output_path_linguistics, "w", encoding="utf-8") as f:
        json.dump(asdict(mapped_doc), f, ensure_ascii=False, indent=4)
    print("[converter_linguistics] JSON lingwistyczny wygenerowany")
else:
    print("[converter_linguistics] nie wygenerowano pliku JSON")