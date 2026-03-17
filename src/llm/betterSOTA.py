import requests
import json
from pathlib import Path

from get_content import get_content, ChapterBlock

MODEL = "SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M"

PROMPT_EVALUATE = """Jesteś ekspertem analizującym strukturę prac naukowych. 
Twoim zadaniem jest ocenić, czy podany rozdział stanowi SOTA (State of the Art / Przegląd literatury / Stan obecny).

Rozdział SOTA charakteryzuje się:
1. Odwołaniami do literatury przedmiotu i innych badań (np. [1], [2], nazwiska autorów).
2. Analizą i porównaniem istniejących na rynku lub w nauce rozwiązań, metod lub technologii.
3. Wskazywaniem luk w obecnej wiedzy lub opisywaniem historii problemu.
4. Jest to CIĄGŁY TEKST (narracja), a nie lista punktów, spis nagłówków czy bibliografia.

Tytuł ocenianego rozdziału: {title}
Fragment treści: {content}

Zwróć wynik WYŁĄCZNIE w formacie JSON o następującej strukturze:
{{
  "czy_sota": true lub false,
  "pewnosc_procentowa": liczba całkowita od 0 do 100,
  "uzasadnienie": "Krótkie, jednozdaniowe uzasadnienie decyzji"
}}
"""

def evaluate_chapter_with_llm(block: ChapterBlock) -> dict:
    truncated_content = block.content[:4000]
    
    prompt = PROMPT_EVALUATE.format(
        title=block.title if block.title else "Brak tytułu",
        content=truncated_content
    )

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json", 
                "options": {
                    "temperature": 0.0,
                    "top_p": 0.1
                }
            },
            timeout=120
        )
        resp.raise_for_status()
        
        response_text = resp.json()["response"]
        data = json.loads(response_text)
        
        return {
            "czy_sota": data.get("czy_sota", False),
            "pewnosc_procentowa": data.get("pewnosc_procentowa", 0),
            "uzasadnienie": data.get("uzasadnienie", "Brak uzasadnienia")
        }
        
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"  [Błąd podczas oceny rozdziału {block.id}]: {e}")
        return {"czy_sota": False, "pewnosc_procentowa": 0, "uzasadnienie": "Błąd API"}

def find_sota_chapter(path: str, output_dir: str = "."):
    print(f"Rozpoczynam wczytywanie pliku: {path}")
    
    blocks = get_content(path)
    print(f"Znaleziono {len(blocks)} potencjalnych rozdziałów/sekcji. Rozpoczynam ocenę AI...\n")

    sota_chapters = []
    THRESHOLD = 85
    
    BLACKLIST = [
        "spis treści", "bibliografia", "spis rysunków", "spis tabel", 
        "streszczenie", "abstract", "lista skrótów", "załącznik", "literatura",
        "indeks", "opis dyplomu", "oświadczenie"
    ]

    for block in blocks:
        if len(block.content) < 200:
            continue
            
        title_lower = block.title.lower() if block.title else ""
        if any(bad_word in title_lower for bad_word in BLACKLIST):
            print(f"-> Analiza Bloku {block.id}: {block.title[:50]}... [POMINIĘTO - SEKCJA TECHNICZNA]")
            continue
            
        print(f"-> Analiza Bloku {block.id}: {block.title[:50]}...")
        evaluation = evaluate_chapter_with_llm(block)
        
        score = evaluation["pewnosc_procentowa"]
        print(f"   Wynik: {score}% | SOTA: {evaluation['czy_sota']} | Powód: {evaluation['uzasadnienie']}")
        
        if score >= THRESHOLD and evaluation['czy_sota']:
            sota_chapters.append({
                "id": block.id,
                "title": block.title,
                "score": score
            })

    summary_lines = ["\n"]
    if sota_chapters:
        summary_lines.append(f"WYNIK ANALIZY: ZNALEZIONO {len(sota_chapters)} ROZDZIAŁÓW SOTA")
        for ch in sota_chapters:
            summary_lines.append(f" - [ID: {ch['id']}] {ch['title']} (Pewność: {ch['score']}%)")
    else:
        summary_lines.append("Nie znaleziono jednoznacznego rozdziału SOTA w tej pracy.")

    summary_text = "\n".join(summary_lines)
    
    print(summary_text)

    out_folder = Path(output_dir)
    out_folder.mkdir(parents=True, exist_ok=True)
    output_filename = out_folder / (Path(path).stem + "_sota_results.txt")
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(summary_text)
    
    print(f"\nZapisano podsumowanie do pliku: {output_filename.absolute()}")

if __name__ == "__main__": 
    file_path = "pdf_diploma_checker/src/theses/ch.pdf"
    folder_docelowy = "pdf_diploma_checker/src/llm/wyniki"
    
    if Path(file_path).exists():
        find_sota_chapter(file_path, output_dir=folder_docelowy)
    else:
        print(f"Błąd: Nie znaleziono pliku {file_path}")