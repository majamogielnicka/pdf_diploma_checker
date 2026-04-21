import requests
import json
from pathlib import Path

from get_content import get_content, ChapterBlock
from extract_citations import analyze_sota_citations, extract_citations
from evaluate_sota import analyze_sota_chapter, print_sota_report

MODEL_PL = "gemma3:4b"
MODEL_EN = "gemma3:4b"

PROMPT_EVALUATE_PL = """Jesteś ekspertem analizującym strukturę prac naukowych. 
Twoim zadaniem jest ocenić, czy podany rozdział stanowi SOTA (State of the Art / Przegląd literatury / Stan obecny).

Rozdział SOTA charakteryzuje się:
1. Odwołaniami do literatury przedmiotu i innych badań (np. [1], [2], nazwiska autorów).
2. Analizą i porównaniem istniejących na rynku lub w nauce rozwiązań, metod lub technologii.
3. Wskazywaniem luk w obecnej wiedzy lub opisywaniem historii problemu.
4. Jest to CIĄGŁY TEKST (narracja), a nie lista punktów, spis nagłówków czy bibliografia.

CZEGO UNIKAĆ (To NIE JEST SOTA):
- Rozdziały techniczne i organizacyjne (np. opis struktury pracy, podział ról w zespole, instrukcje obsługi, opis działania stworzonej aplikacji).
- Słowniki pojęć, wykazy skrótów, spisy tabel.
- Zwykłe wymienianie bibliografii bez narracji.

Tytuł ocenianego rozdziału: {title}
Fragment treści: {content}

Zwróć wynik WYŁĄCZNIE w formacie JSON o następującej strukturze:
{{
  "czy_sota": true lub false,
  "pewnosc_procentowa": liczba całkowita od 0 do 100,
  "uzasadnienie": "Krótkie, jednozdaniowe uzasadnienie decyzji"
}}
"""

PROMPT_EVALUATE_EN = """You are an expert analyzing the structure of academic papers.
Your task is to evaluate whether the provided chapter represents the SOTA (State of the Art / Literature Review / Current State).

A SOTA chapter is characterized by:
1. References to literature and other research (e.g., [1], [2], authors' names).
2. Analysis and comparison of existing solutions, methods, or technologies in the market or science.
3. Pointing out gaps in current knowledge or describing the history of the problem.
4. It is CONTINUOUS TEXT (narrative), not a bulleted list, table of contents, or bibliography.

WHAT TO AVOID (This is NOT SOTA):
- Technical and organizational chapters (e.g., description of thesis structure, division of roles, user manuals, application description).
- Glossaries, list of abbreviations, list of tables.
- Mere listing of bibliography without narrative.

Title of the evaluated chapter: {title}
Content snippet: {content}

Return the result EXCLUSIVELY in JSON format with the following structure:
{{
  "czy_sota": true or false,
  "pewnosc_procentowa": integer from 0 to 100,
  "uzasadnienie": "Short, one-sentence justification for the decision"
}}
"""

def evaluate_chapter_with_llm(block: ChapterBlock, language: str) -> dict:
    truncated_content = block.content[:4000]
    
    if language == "pl":
        prompt = PROMPT_EVALUATE_PL.format(title=block.title if block.title else "Brak", content=truncated_content)
        model_to_use = MODEL_PL
    else:
        prompt = PROMPT_EVALUATE_EN.format(title=block.title if block.title else "None", content=truncated_content)
        model_to_use = MODEL_EN

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model_to_use, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.0, "top_p": 0.1}},
            timeout=120
        )
        resp.raise_for_status()
        data = json.loads(resp.json()["response"])
        return {
            "czy_sota": data.get("czy_sota", False),
            "pewnosc_procentowa": data.get("pewnosc_procentowa", 0),
            "uzasadnienie": data.get("uzasadnienie", "Brak uzasadnienia")
        }
    except Exception as e:
        print(f"  [Błąd AI w bloku {block.id}]: {e}")
        return {"czy_sota": False, "pewnosc_procentowa": 0, "uzasadnienie": "Błąd API"}


def find_sota_chapter(path: str, language: str = "pl", output_dir: str = "."):
    print(f"\nRozpoczynam wczytywanie pliku: {path}")
    blocks = get_content(path)
    print(f"Znaleziono {len(blocks)} potencjalnych rozdziałów. Szukam 1 najlepszego...\n")

    if language == "pl":
        BLACKLIST = [
            "spis treści", "bibliografia", "spis rysunków", "spis tabel", 
            "streszczenie", "abstract", "lista skrótów", "załącznik", "literatura",
            "indeks", "opis dyplomu", "oświadczenie", "opis pracy", "cel pracy",
            "wstęp", "zakończenie", "podsumowanie"
        ]
        SOTA_KEYWORDS = [
            "przegląd literatury", "stan wiedzy", "state of the art", "sota", 
            "przegląd rozwiązań", "istniejące rozwiązania", "analiza literatury",
            "podbudowa teoretyczna", "przegląd badań", "przegląd technologii",
            "stan obecny"
        ]
    else:
        BLACKLIST = [
            "table of contents", "bibliography", "list of figures", "list of tables",
            "abstract", "abbreviations", "appendix", "references", "index",
            "declaration", "introduction", "conclusion", "summary", "thesis overview"
        ]
        SOTA_KEYWORDS = [
            "literature review", "state of the art", "sota", "existing solutions",
            "related work", "background", "theoretical background", "technology review"
        ]

    valid_blocks = []
    for block in blocks:
        if len(block.content) < 200:
            continue
        title_lower = block.title.lower() if block.title else ""
        if any(bad_word in title_lower for bad_word in BLACKLIST):
            print(f"-> Odrzucono (Blacklista): {block.title[:50]}...")
            continue
        valid_blocks.append(block)

    sota_chapter = None
    selection_method = ""
    is_fallback = False
    fallback_reason = ""
    best_llm_candidate = None

    for block in valid_blocks:
        title_lower = block.title.lower() if block.title else ""
        if any(kw in title_lower for kw in SOTA_KEYWORDS):
            sota_chapter = block
            selection_method = "KROK 1 (Słowa kluczowe w tytule)"
            print(f"\n[SUKCES KROK 1] Znaleziono SOTA na podstawie tytułu: '{block.title}'")
            break

    if not sota_chapter:
        print(f"\n[INFO] Nie znaleziono po tytule. Uruchamiam analizę AI ({'Bielik' if language == 'pl' else 'Qwen'})...")
        llm_candidates = []
        THRESHOLD = 90 
        
        for block in valid_blocks:
            print(f"-> Analiza AI Bloku {block.id}: {block.title[:50]}...")
            evaluation = evaluate_chapter_with_llm(block, language)
            score = evaluation["pewnosc_procentowa"]
            print(f"   Wynik: {score}% | SOTA: {evaluation['czy_sota']} | Powód: {evaluation['uzasadnienie']}")
            
            if score >= THRESHOLD and evaluation['czy_sota']:
                llm_candidates.append({
                    "block": block,
                    "score": score,
                    "reason": evaluation['uzasadnienie']
                })
                
        if llm_candidates:
            perfect_candidates = [c for c in llm_candidates if c["score"] == 100]
            
            if perfect_candidates:
                best_llm_candidate = perfect_candidates[0]
                sota_chapter = best_llm_candidate["block"]
                selection_method = "KROK 2 (Analiza AI - Pewność 100%)"
                print(f"\n[SUKCES KROK 2] LLM przyznał 100% pewności: '{sota_chapter.title}'")
            else:
                print("\n[INFO] AI wskazało kandydatów (>= 90%), ale bez 100% pewności. Decyduje liczba unikalnych cytowań...")
                max_cites = -1
                
                for c in llm_candidates:
                    cites = len(set(extract_citations(c["block"].content)))
                    print(f"   -> LLM Kandydat: '{c['block'].title[:40]}...' | Pewność: {c['score']}% | Unikalne cytowania: {cites}")
                    if cites > max_cites:
                        max_cites = cites
                        best_llm_candidate = c
                        
                if best_llm_candidate:
                    sota_chapter = best_llm_candidate["block"]
                    selection_method = f"KROK 2 + CYTOWANIA (Pewność LLM: {best_llm_candidate['score']}%, Cytowań: {max_cites})"
                    print(f"\n[SUKCES KROK 2/3] Wytypowano SOTA na podstawie cytowań spośród faworytów AI: '{sota_chapter.title}'")

    if not sota_chapter:
        print("\n[INFO] AI nie znalazło SOTA (brak wyników >= 90%). Rozpoczynam liczenie przypisów jako wariant awaryjny...")
        is_fallback = True
        max_unique = -1
        best_block = None
        
        for block in valid_blocks:
            citations = extract_citations(block.content)
            unique_count = len(set(citations))
            
            if unique_count > max_unique:
                max_unique = unique_count
                best_block = block
                
        if best_block and max_unique > 0:
            sota_chapter = best_block
            selection_method = "KROK 3 (Najwięcej unikalnych cytowań w całej pracy)"
            fallback_reason = f"zawiera najwięcej unikalnych cytowań w całej pracy ({max_unique})."
            print(f"\n[SUKCES KROK 3 - FALLBACK] Wybrano awaryjnie SOTA: '{sota_chapter.title}'")

    summary_lines = ["\n" + "="*50]
    if sota_chapter:
        summary_lines.append("WYNIK ANALIZY SOTA (Wybrano 1 rozdział):")
        summary_lines.append(f" - [ID: {sota_chapter.id}] {sota_chapter.title}")
        summary_lines.append(f" - Metoda wyboru: {selection_method}")
        
        if not is_fallback and not best_llm_candidate:
            summary_lines.append("\nUzasadnienie: Rozdział posiadał tytuł wskazujący bezpośrednio na przegląd wiedzy.")
        elif best_llm_candidate and best_llm_candidate["score"] == 100:
            summary_lines.append(f"\nUzasadnienie AI (Pewność 100%): {best_llm_candidate['reason']}")
        elif best_llm_candidate:
            summary_lines.append(f"\nUzasadnienie: Wybrano na podstawie wysokiej oceny AI ({best_llm_candidate['score']}%) i przewagi w liczbie cytowań.")
        elif is_fallback:
            summary_lines.append(f"\nUzasadnienie: Nie wykryto SOTA semantycznie. Wybrano ten rozdział, ponieważ {fallback_reason}")
    else:
        summary_lines.append("Nie znaleziono żadnego rozdziału SOTA w tej pracy (brak odpowiednich tytułów, przypisów i treści).")
    summary_lines.append("="*50)

    summary_text = "\n".join(summary_lines)
    print(summary_text)

    out_folder = Path(output_dir)
    out_folder.mkdir(parents=True, exist_ok=True)
    output_filename = out_folder / (Path(path).stem + "_sota_results.txt")
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(summary_text)
    
    print(f"\nZapisano podsumowanie do pliku: {output_filename.absolute()}")

    if sota_chapter:
        print(f"\nPrzekazuję wykryte ID ([{sota_chapter.id}]) do skryptu cytowań...")
        analyze_sota_citations(path, [sota_chapter.id], output_dir)

    if sota_chapter:
        print(f"\nPrzekazuję wykryte ID ([{sota_chapter.id}]) do szczegółowej oceny SOTA...")
        ocena = analyze_sota_chapter(sota_chapter.id, sota_chapter.title, path)
        print_sota_report(ocena)

if __name__ == "__main__":
    test_file_path = "data/jago.pdf"
    test_language = "pl" 
    test_output_dir = "src/llm/wynikiSOTA"
    
    print(f"--- URUCHAMIANIE TRYBU TESTOWEGO DLA: {test_file_path} ({test_language}) ---")
    if Path(test_file_path).exists():
        find_sota_chapter(test_file_path, language=test_language, output_dir=test_output_dir)
        print("\n--- TEST ZAKOŃCZONY ---")
    else:
        print(f"BŁĄD: Nie znaleziono pliku {test_file_path}.")