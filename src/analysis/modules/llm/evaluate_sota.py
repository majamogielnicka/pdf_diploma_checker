import json
import requests
from typing import Dict, Any
from get_content import get_content

MODEL_NAME = "gemma3:4b"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

def ask_llm(prompt: str, content: str) -> bool:
    full_prompt = f"{prompt}\n\nTekst rozdziału:\n{content}\n\nZwróć odpowiedź WYŁĄCZNIE w formacie JSON: {{\"wynik\": true/false}}"
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0, "top_p": 0.1}
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = json.loads(response.json()["response"])
        return data.get("wynik", False)
    except Exception:
        return False

def evaluate_r1(content: str) -> int:
    prompt = "Czy podany tekst zawiera wyraźną ocenę, krytykę, wskazywanie wad i zalet istniejących rozwiązań?"
    return 1 if ask_llm(prompt, content) else 0

def evaluate_r2(content: str) -> int:
    prompt = "Czy podany tekst jednoznacznie wskazuje lukę badawczą lub konkretny problem naukowy do rozwiązania?"
    return 1 if ask_llm(prompt, content) else 0

def evaluate_r3(content: str) -> int:
    prompt = "Czy podany tekst zawiera syntezę lub bezpośrednie porównanie co najmniej dwóch różnych metod lub podejść?"
    return 1 if ask_llm(prompt, content) else 0

def get_sota_status(score: int) -> str:
    if score >= 2:
        return "Pełna realizacja SOTA"
    elif score == 1:
        return "Częściowa realizacja SOTA"
    return "Brak poprawnej sekcji SOTA"

def calculate_sota_percentage(score: int) -> int:
    if score >= 2:
        return 100
    elif score == 1:
        return 50
    return 0

def fetch_chapter_content(file_path: str, chapter_id: str) -> str:
    blocks = get_content(file_path)
    for block in blocks:
        if block.id == chapter_id:
            return block.content
    return ""

def analyze_sota_chapter(chapter_id: str, chapter_title: str, file_path: str) -> Dict[str, Any]:
    content = fetch_chapter_content(file_path, chapter_id)
    if not content:
        raise ValueError(f"Nie znaleziono rozdziału {chapter_id} w pliku {file_path}")

    truncated_content = content[:4000]

    r1_score = evaluate_r1(truncated_content)
    r2_score = evaluate_r2(truncated_content)
    r3_score = evaluate_r3(truncated_content)
    
    total_score = r1_score + r2_score + r3_score
    status = get_sota_status(total_score)
    percentage = calculate_sota_percentage(total_score)
    
    return {
        "tytul": chapter_title,
        "r1": r1_score,
        "r2": r2_score,
        "r3": r3_score,
        "suma": total_score,
        "status": status,
        "procent": percentage
    }

def print_sota_report(result: Dict[str, Any]):
    print("=" * 60)
    print(f"RAPORT OCENY JAKOŚCI SOTA: {result['tytul']}")
    print("=" * 60)
    print(f"R1 (Ocena istniejących rozwiązań): {'1 - SPEŁNIONO' if result['r1'] else '0 - NIESPEŁNIONO'}")
    print(f"R2 (Wskazanie luki badawczej):     {'1 - SPEŁNIONO' if result['r2'] else '0 - NIESPEŁNIONO'}")
    print(f"R3 (Synteza/porównanie metod):     {'1 - SPEŁNIONO' if result['r3'] else '0 - NIESPEŁNIONO'}")
    print("-" * 60)
    print(f"SUMA PUNKTÓW: {result['suma']}/3")
    print(f"WYNIK PROCENTOWY SOTA: {result['procent']}%")
    print(f"WERDYKT: {result['status']}")
    print("=" * 60)

if __name__ == "__main__":
    TEST_FILE = "src/theses/jago.pdf"
    TEST_CHAPTER_ID = "2.1"
    TEST_TITLE = "Modele emocji"
    
    try:
        print(f"Rozpoczynam analizę rozdziału {TEST_CHAPTER_ID}...")
        wynik = analyze_sota_chapter(TEST_CHAPTER_ID, TEST_TITLE, TEST_FILE)
        print_sota_report(wynik)
    except Exception as e:
        print(f"Błąd krytyczny: {e}")