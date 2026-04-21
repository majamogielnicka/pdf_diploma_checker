import json
import re
from typing import Dict, Any, List
from llama_cpp import Llama
from get_content import get_content

# MODEL_PATH = "src/models/gemma-3-4b-it-Q4_K_M.gguf"
MODEL_PATH = "src/models/gemma-3-12b-it-Q4_K_M.gguf"
CHUNK_SIZE = 2500 

_llm_instance = None

def get_llm():
    """Funkcja gwarantująca, że model załaduje się do pamięci tylko raz."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = Llama(
            model_path=MODEL_PATH,
            n_ctx=4096,
            n_gpu_layers=-1,
            verbose=False
        )
    return _llm_instance

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Dzieli długi tekst na mniejsze fragmenty."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def ask_llm(prompt: str, content: str) -> bool:
    full_prompt = f"{prompt}\n\nTekst fragmentu rozdziału:\n{content}\n\nZwróć odpowiedź WYŁĄCZNIE w formacie JSON według wzoru:\n{{\"uzasadnienie\": \"krótkie wyjaśnienie\", \"wynik\": true lub false}}"
    
    try:
        response = get_llm().create_chat_completion(
            messages=[
                {"role": "system", "content": "Jesteś surowym recenzentem. Zwracaj tylko obiekt JSON. Żadnych wstępów. Żadnych znaczników ```json."},
                {"role": "user", "content": full_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            top_p=0.1,
            max_tokens=150
        )
        result_text = response["choices"][0]["message"]["content"].strip()
        
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        result_text = result_text.strip()
        
        try:
            data = json.loads(result_text)
            wynik = data.get("wynik", False)
            if isinstance(wynik, str):
                return wynik.lower() == "true"
            return bool(wynik)
            
        except json.JSONDecodeError:
            print("  [Ostrzeżenie] Czyszczenie JSON nie pomogło, analizuję tekst regexem...")
            surowy_tekst = result_text.lower()
            if re.search(r'"wynik"\s*:\s*"?true"?', surowy_tekst) or re.search(r'wynik\s*:\s*"?true"?', surowy_tekst):
                return True
            return False
            
    except Exception as e:
        print(f"Błąd krytyczny LLM: {e}")
        return False

def evaluate_condition_over_chunks(prompt: str, chunks: List[str]) -> int:
    """
    Przepuszcza zapytanie przez kolejne fragmenty tekstu.
    Zatrzymuje się i zwraca 1 od razu, gdy tylko znajdzie potwierdzenie w którymś fragmencie.
    Jeśli żaden fragment nie spełni warunku, zwraca 0.
    """
    for chunk in chunks:
        result = ask_llm(prompt, chunk)
        if result is True:
            return 1 
    return 0

def evaluate_r1(chunks: List[str]) -> int:
    prompt = """Twoim zadaniem jest ocenić, czy podany fragment tekstu spełnia regułę R1.
Reguła R1: Czy fragment zawiera wyraźną ocenę (parametry, skuteczność) lub wskazuje konkretne WADY/ZALETY istniejących, działających rozwiązań?

UWAGA KRYTYCZNA - NIE MYL R1 Z LUKĄ BADAWCZĄ:
- Słowa takie jak "brakuje badań", "luka w wiedzy", "nie wiadomo", "nierozwiązany problem" to NIE SĄ wady technologii! To są luki badawcze (które należą do innej reguły). 
- Nie przyznawaj R1 za to, że autor pisze, czego w nauce jeszcze nie zbadano.

KRYTERIA:
- ZWRÓĆ TRUE TYLKO wtedy, gdy fragment chwali działające systemy (np. "redukuje czas o 18%") lub wylicza ich znane techniczne wady (np. "bateria działa krótko").
- ZWRÓĆ FALSE, jeśli fragment skupia się wyłącznie na brakach w wiedzy, braku ram prawnych czy niewiadomych, które dopiero trzeba zbadać.
- ZWRÓĆ FALSE, jeśli to tylko suchy opis działania."""
    
    return evaluate_condition_over_chunks(prompt, chunks)

def evaluate_r2(chunks: List[str]) -> int:
    prompt = """Twoim zadaniem jest ocenić, czy podany fragment tekstu spełnia regułę R2.
Reguła R2: Czy fragment JEDNOZNACZNIE wskazuje LUKĘ BADAWCZĄ w nauce lub NIEROZWIĄZANY problem naukowy?

UWAGA KRYTYCZNA:
Nie myl "problemu, który technologia już rozwiązuje" (np. zanieczyszczenia powietrza, awarie sieci) z "luką badawczą". 

KRYTERIA (Bądź bezlitosny):
- ZWRÓĆ FALSE, jeśli fragment opisuje technologie, które z powodzeniem rozwiązują jakieś problemy (np. "technologie te stanowią dojrzałe rozwiązania").
- ZWRÓĆ TRUE TYLKO WTEDY, gdy autor wyraźnie pisze, że czegoś W NAUCE JESZCZE NIE WIADOMO, brakuje badań lub coś wymaga dalszych analiz naukowych (np. "Brakuje badań nad...", "Niewiadomą pozostaje...")."""
    
    return evaluate_condition_over_chunks(prompt, chunks)

def evaluate_r3(chunks: List[str]) -> int:
    prompt = """Twoim zadaniem jest ocenić, czy podany fragment tekstu spełnia regułę R3.
Reguła R3: Czy fragment zawiera BEZPOŚREDNIE PORÓWNANIE co najmniej dwóch NAZWANYCH, RÓŻNYCH METOD rozwiązujących ten sam problem?

UWAGA KRYTYCZNA:
Podawanie skuteczności (np. "system redukuje korki o 18%") TO NIE JEST PORÓWNANIE METOD! To tylko opis skuteczności jednego systemu. Aby było to porównanie, autor musi dosłownie zestawić dwie metody.

KRYTERIA:
- ZWRÓĆ TRUE TYLKO WTEDY, gdy we fragmencie walczą ze sobą dwie metody (np. "Metoda X jest lepsza niż Metoda Y w warunkach miejskich").
- ZWRÓĆ FALSE, jeśli fragment to wyliczanka świetnie działających systemów z różnych dziedzin. To nie jest zderzenie metod!"""
    
    return evaluate_condition_over_chunks(prompt, chunks)

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
        if str(block.id) == str(chapter_id):
            return block.content
    return ""

def analyze_sota_chapter(chapter_id: str, chapter_title: str, file_path: str) -> Dict[str, Any]:
    """Zwraca słownik z kompletną oceną rozdziału, analizując cały tekst w porcjach."""
    content = fetch_chapter_content(file_path, chapter_id)
    if not content:
        raise ValueError(f"Nie znaleziono rozdziału {chapter_id} w pliku {file_path}")

    chunks = chunk_text(content)

    r1_score = evaluate_r1(chunks)
    r2_score = evaluate_r2(chunks)
    r3_score = evaluate_r3(chunks)
    
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
