# 1. Zaimportuj potrzebne klasy (zakładam, że masz je w swoich plikach)
from src.analysis.extraction.bare_struct import DocumentData
# import twojego walidatora (zależnie od tego, jak nazwałeś plik, np. z pliku validator.py)
from src.analysis.extraction.redaction_validator import RedactionValidator
# Zakładam, że masz już jakąś funkcję, która parsuje PDF i zwraca DocumentData
# document_data = extract_data_from_pdf("sciezka/do/dokumentu.pdf")

# Na potrzeby przykładu udajemy, że mamy już gotowy obiekt document_data:
document_data = DocumentData(...) 

# 2. Tworzymy instancję walidatora
validator = RedactionValidator(document_data)

# 3. Uruchamiamy walidację
found_errors = validator.validate()

# 4. Sprawdzamy wyniki
if not found_errors:
    print("Super! Nie znaleziono błędów z redakcją (brak sierotek i pustych stron).")
else:
    print(f"Znaleziono {len(found_errors)} błędów:")
    for error in found_errors:
        print(f"[{error.id}] Typ: {error.category}, Strona: {error.page_nr}")
        if error.category == "orphan":
            print(f"  -> Sierotka: '{error.text}' w obszarze: {error.bounding_box}")
        print(f"  -> Komentarz: {error.comments}")
        print("-" * 40)