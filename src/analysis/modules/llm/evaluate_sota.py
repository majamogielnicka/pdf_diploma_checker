import json
from typing import Dict, Any
from llama_cpp import Llama
from get_content import get_content

MODEL_PATH = "src/models/gemma-3-4b-it-Q4_K_M.gguf"

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

def ask_llm(prompt: str, content: str) -> bool:
    full_prompt = f"{prompt}\n\nTekst rozdziału:\n{content}\n\nZwróć odpowiedź WYŁĄCZNIE w formacie JSON: {{\"wynik\": true/false}}"
    
    try:
        response = get_llm().create_chat_completion(
            messages=[
                {"role": "system", "content": "Zwracaj wyłącznie poprawny format JSON."},
                {"role": "user", "content": full_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            top_p=0.1,
            max_tokens=50
        )
        result_text = response["choices"][0]["message"]["content"]
        data = json.loads(result_text)
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
        if str(block.id) == str(chapter_id):
            return block.content
    return ""

def analyze_sota_chapter(chapter_id: str, chapter_title: str, file_path: str) -> Dict[str, Any]:
    """Zwraca słownik z kompletną oceną rozdziału."""
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