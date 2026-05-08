from get_content import get_content
from find_sota import get_sota_chapter
from evaluate_sota import analyze_sota_chapter

from config import THESIS_PATH, LANGUAGE

def get_final_sota_report(blocks: list, language: str = LANGUAGE):
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

    s_id, s_title, s_method, s_citations, s_content = get_sota_chapter(blocks, language)
    
    if not s_id:
        return None, None, 0, "Brak", 0, False, False, False

    try:
        ocena_data = analyze_sota_chapter(s_title, s_content)
        
        s_score = int(ocena_data["procent"])
        r1 = bool(ocena_data["r1"])
        r2 = bool(ocena_data["r2"])
        r3 = bool(ocena_data["r3"])
        
    except Exception as e:
        print(f"Błąd analizy: {e}")
        s_score = 0
        r1 = r2 = r3 = False

    return s_id, s_title, s_score, s_method, s_citations, r1, r2, r3

if __name__ == "__main__":
    print(f"Rozpoczynam analizę z konfiguracji: {THESIS_PATH}")
    
    extracted_blocks = get_content(THESIS_PATH)

    res_id, res_title, res_score, res_method, res_cites, r1, r2, r3 = get_final_sota_report(extracted_blocks, LANGUAGE)
    
    print(f"\n--- WYNIKI ---")
    print(f"ID: {res_id}")
    print(f"Tytuł: {res_title}")
    print(f"Wynik: {res_score}%")
    print(f"Podstawa wyboru: {res_method}")
    print(f"R1: {r1}, R2: {r2}, R3: {r3}")