from find_sota import get_sota_chapter
from evaluate_sota import analyze_sota_chapter

def get_final_sota_report(pdf_path: str, language: str = "pl"):
    """
    ZWRACA 8 WARTOŚCI:
    1) id (str)
    2) tytul (str)
    3) ocena (int: 0, 50, 100)
    4) podstawa_wyboru (str)
    5) liczba_cytowan (int)
    6) r1 (bool) - ocena istniejących rozwiązań
    7) r2 (bool) - wskazanie luki/problemu
    8) r3 (bool) - synteza/porównanie metod
    """
    s_id, s_title, s_method, s_citations = get_sota_chapter(pdf_path, language)
    
    if not s_id:
        return None, None, 0, "Brak", 0, False, False, False

    try:
        ocena_data = analyze_sota_chapter(s_id, s_title, pdf_path)
        
        s_score = int(ocena_data["procent"])
        r1 = bool(ocena_data["r1"])
        r2 = bool(ocena_data["r2"])
        r3 = bool(ocena_data["r3"])
        
    except Exception:
        s_score = 0
        r1 = r2 = r3 = False

    return s_id, s_title, s_score, s_method, s_citations, r1, r2, r3

if __name__ == "__main__":

    path = "data/jabi.pdf"

    #Przykład użycia:
    res_id, res_title, res_score, res_method, res_cites, r1, r2, r3 = get_final_sota_report(path)
    
    print(f"ID: {res_id}")
    print(f"Tytuł: {res_title}")
    print(f"Wynik: {res_score}%")
    print(f"Podstawa wyboru: {res_method}")
    print(f"R1: {r1}, R2: {r2}, R3: {r3}") 

# Wyjaśnienie reguł oceny SOTA
# r1 — zawiera ocenę istniejących rozwiązań,
# r2 — wskazuje lukę badawczą lub problem,
# r3 — zawiera syntezę lub porównanie metod i podejść.

# Przykładowa odpowiedź:
# ID: 10
# Tytuł: PRZEGLĄD ROZWIĄZAŃ (JAKUB BIEŃKOWSKI, JAKUB MAKOWSKI)
# Wynik: 100%
# Podstawa wyboru: KROK 1 (Słowa kluczowe w tytule)
# R1: True, R2: True, R3: True