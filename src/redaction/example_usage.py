'''-----------------------przykład dla extraction_json.py-----------------------'''
from pathlib import Path
from extraction_json import extractPDF

input_path = Path("pdf_diploma_checker/src/theses/kana.pdf")
output_path = Path("pdf_diploma_checker/src/output.json")

# Tryb debugu:
# 0 - domyślny tryb, program działakorzystając z /thesis
# 1 - tryb debugowania, ułatwia pracę nad konkretną funkcjonalnością, korzysta z /redaction_debug
# TODO: dodać więcej przykładowych plików pdf do folderu /redaction_debug
# Format nazwy pdfa: <aspekt_do_sprawdzenia>_example.pdf
debug_mode = 0
debug_type = "table" # zmiana trybu debugowania (wpisać interesujący nas aspekt)
debug_path = "pdf_diploma_checker/src/redaction/redaction_debug/{debug_type}_example.pdf"


#test:
#print(extractPDF("1.pdf").to_dict())

if debug_mode == 0:
    pdf_path = Path(input_path)
elif debug_mode == 1:
    candidate = Path(debug_path.format(debug_type=debug_type))
    if candidate.exists():
        pdf_path = candidate
    else:
        print(f"Debug PDF not found: {candidate}. Falling back to default thesis path.")
        pdf_path = Path("src/theses/gp.pdf")

doc_data = extractPDF(pdf_path)

#TODO: dodac warunek sprqwdzjaacy blad do testow
doc_data.to_json(output_path) 

'''-----------------------przykład dla converter_linguistics.py-----------------------'''
from pathlib import Path
from converter_linguistics import PDFMapper
pdf_path = Path("pdf_diploma_checker/src/theses/kana.pdf")

if pdf_path.exists():
    raw_data = extractPDF(str(pdf_path))
    final_doc = PDFMapper.map_to_schema(raw_data)
    final_doc.to_json("pdf_diploma_checker/src/redaction/output.json")
    print("JSON wygenerowany")
else:
    print(f"Błąd: Nie znaleziono pliku {pdf_path}")