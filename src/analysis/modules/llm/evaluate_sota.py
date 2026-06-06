import json
import re
from typing import Dict, Any, List
from llama_cpp import Llama

from config import MODEL_PATH, N_GPU_LAYERS

CHUNK_SIZE = 2500 

_llm_instance = None

def get_llm():
    """Return LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=4096,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False
        )
    return _llm_instance

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split long text into fixed-size chunks."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def ask_llm(prompt: str, content: str) -> bool:
    """Evaluate a single chunk with the LLM and return a boolean verdict."""
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
    """Return 1 if any chunk satisfies the condition, otherwise 0."""
    for chunk in chunks:
        result = ask_llm(prompt, chunk)
        if result is True:
            return 1 
    return 0

def evaluate_r1(chunks: List[str]) -> int:
    """Evaluate rule R1 across all chunks."""
    prompt = """Twoim zadaniem jest ocenić, czy podany fragment tekstu spełnia regułę R1.
Reguła R1: Czy fragment zawiera wyraźną ocenę (parametry, skuteczność) lub wskazuje konkretne WADY/ZALETY istniejących, działających rozwiązań?
[... reszta promptu ...]"""
    return evaluate_condition_over_chunks(prompt, chunks)

def evaluate_r2(chunks: List[str]) -> int:
    """Evaluate rule R2 across all chunks."""
    prompt = """Twoim zadaniem jest ocenić, czy podany fragment tekstu spełnia regułę R2.
Reguła R2: Czy fragment JEDNOZNACZNIE wskazuje LUKĘ BADAWCZĄ w nauce lub NIEROZWIĄZANY problem naukowy?
[... reszta promptu ...]"""
    return evaluate_condition_over_chunks(prompt, chunks)

def evaluate_r3(chunks: List[str]) -> int:
    """Evaluate rule R3 across all chunks."""
    prompt = """Twoim zadaniem jest ocenić, czy podany fragment tekstu spełnia regułę R3.
Reguła R3: Czy fragment zawiera BEZPOŚREDNIE PORÓWNANIE co najmniej dwóch NAZWANYCH, RÓŻNYCH METOD rozwiązujących ten sam problem?
[... reszta promptu ...]"""
    return evaluate_condition_over_chunks(prompt, chunks)

def get_sota_status(score: int) -> str:
    """Map raw rule score to a human-readable SOTA status."""
    if score >= 2: return "Pełna realizacja SOTA"
    elif score == 1: return "Częściowa realizacja SOTA"
    return "Brak poprawnej sekcji SOTA"

def calculate_sota_percentage(score: int) -> int:
    """Convert the raw SOTA score to a percentage."""
    if score >= 2: return 100
    elif score == 1: return 50
    return 0

def analyze_sota_chapter(chapter_title: str, content: str) -> Dict[str, Any]:
    """Return a complete SOTA assessment dictionary for a chapter."""
    if not content:
        raise ValueError(f"Nie przekazano treści dla rozdziału: {chapter_title}")

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

def free_sota_memory():
    """Release SOTA model resources and trigger garbage collection."""
    global _llm_instance
    if _llm_instance is not None:
        del _llm_instance
        _llm_instance = None
        import gc
        gc.collect()
        print("[AI] Pamięć GPU po module SOTA została wyczyszczona.")