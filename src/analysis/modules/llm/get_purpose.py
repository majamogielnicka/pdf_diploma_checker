import sys
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

from analysis.extraction.converter_linguistics import get_plain_text

file_path = PROJECT_ROOT / "data" / "kana.pdf"
language = "en"

MODEL_NAME = "gemma3local"
OUTPUT_DIR = BASE_DIR / "wyniki"

CHUNK_SIZE = 2000
MAX_CHUNKS = 20
REQUEST_TIMEOUT = 600


def ask_ollama(prompt, num_predict=60):
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "15m",
            "options": {
                "temperature": 0.0,
                "num_predict": num_predict,
                "top_p": 0.2,
                "num_ctx": 4096
            }
        },
        timeout=REQUEST_TIMEOUT
    )

    if not resp.ok:
        raise requests.exceptions.HTTPError(
            f"{resp.status_code}: {resp.text}",
            response=resp
        )

    return resp.json().get("response", "").strip()


def normalize_text(text):
    if not text:
        return ""
    return " ".join(str(text).split()).strip()


def prepare_text(path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_text = get_plain_text(path)
    plain_text_path = OUTPUT_DIR / f"{path.stem}_plain_text.txt"
    plain_text_path.write_text(raw_text, encoding="utf-8")
    return normalize_text(raw_text)


def split_into_chunks(text, chunk_size=CHUNK_SIZE, max_chunks=MAX_CHUNKS):
    text = text[: chunk_size * max_chunks].strip()
    chunks = []

    start = 0
    while start < len(text) and len(chunks) < max_chunks:
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        start = end

    return [chunk for chunk in chunks if chunk]


def build_candidate_prompt_pl(content):
    return f"""
Wyodrębnij z fragmentu wyłącznie treść głównego celu pracy.

Zasady:
- odpowiedź tylko po polsku
- jeśli da się ustalić cel, zwróć wyłącznie jedną frazę rzeczownikową
- nie zwracaj pełnego zdania
- nie dodawaj żadnego wstępu ani komentarza
- nie używaj form typu: "Celem pracy jest", "Praca ma na celu", "Cel pracy to"
- nie streszczaj tekstu
- nie cytuj dosłownie
- jeśli celu nie da się ustalić wiarygodnie, zwróć dokładnie: BRAK

Poprawna forma odpowiedzi:
analiza wpływu parametrów druku 3D na właściwości mechaniczne i elektryczne materiału
ocena skuteczności wybranej metody w badanej grupie
opracowanie modelu wspomagającego proces decyzyjny

Fragment:
{content}
""".strip()


def build_candidate_prompt_en(content):
    return f"""
Extract only the main thesis purpose from the fragment.

Rules:
- answer only in English
- return only a noun phrase
- do not return a full sentence
- do not start with: this thesis, the thesis, this work, the aim of this thesis, the purpose of this thesis
- do not add any explanation or commentary
- do not summarize the fragment
- if the purpose cannot be determined reliably, return exactly: NONE

Correct form:
optimization of 3D printing parameters for improved electrical conductivity
evaluation of the effectiveness of the selected method in the study group
development of a decision-support model

Fragment:
{content}
""".strip()


def build_final_prompt_pl(candidates):
    joined = "\n".join(f"- {c}" for c in candidates)
    return f"""
Wybierz z poniższych kandydatów jedno najlepsze sformułowanie głównego celu pracy.

Zasady:
- odpowiedź tylko po polsku
- zwróć wyłącznie jedną krótką frazę rzeczownikową
- nie zwracaj pełnego zdania
- nie dodawaj żadnego wstępu ani komentarza
- nie używaj form typu: "Celem pracy jest", "Praca ma na celu", "Cel pracy to"
- nie dodawaj informacji spoza kandydatów
- jeśli żaden kandydat nie jest wiarygodny, zwróć: BRAK

Kandydaci:
{joined}
""".strip()


def build_final_prompt_en(candidates):
    joined = "\n".join(f"- {c}" for c in candidates)
    return f"""
Choose the single best thesis purpose from the candidates below.

Rules:
- answer only in English
- return only a short noun phrase
- do not return a full sentence
- do not start with: this thesis, the thesis, this work, the aim of this thesis, the purpose of this thesis
- do not add any explanation or commentary
- do not add information beyond the candidates
- if none is reliable, return exactly: NONE

Candidates:
{joined}
""".strip()


def normalize_candidate(text):
    return normalize_text(text).strip(" .:-")


def collect_purpose_candidates(text, language="pl"):
    chunks = split_into_chunks(text)
    candidates = []

    for chunk in chunks:
        if language == "pl":
            prompt = build_candidate_prompt_pl(chunk)
            result = normalize_candidate(ask_ollama(prompt, num_predict=60))
            if result and result != "BRAK":
                candidates.append(result)
        else:
            prompt = build_candidate_prompt_en(chunk)
            result = normalize_candidate(ask_ollama(prompt, num_predict=60))
            if result and result != "NONE":
                candidates.append(result)

    unique_candidates = []
    seen = set()

    for candidate in candidates:
        key = candidate.lower()
        if key not in seen:
            seen.add(key)
            unique_candidates.append(candidate)

    return unique_candidates


def get_purpose(path, language="pl"):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

    full_text = prepare_text(path)

    if not full_text:
        return "Błąd: nie udało się odczytać treści pracy."

    try:
        candidates = collect_purpose_candidates(full_text, language)

        if not candidates:
            if language == "pl":
                return "Brak jasno określonego celu pracy."
            return "No clearly defined thesis purpose found."

        if len(candidates) == 1:
            return candidates[0]

        if language == "pl":
            final_prompt = build_final_prompt_pl(candidates)
            result = normalize_candidate(ask_ollama(final_prompt, num_predict=60))
            return result if result else "Brak jasno określonego celu pracy."

        if language == "en":
            final_prompt = build_final_prompt_en(candidates)
            result = normalize_candidate(ask_ollama(final_prompt, num_predict=60))
            if not result or result == "NONE":
                return "No clearly defined thesis purpose found."
            return result

        return "Błąd: nieobsługiwany język."

    except requests.exceptions.ReadTimeout:
        return "Błąd: model nie odpowiedział na czas."
    except requests.exceptions.ConnectionError:
        return "Błąd: nie udało się połączyć z Ollamą."
    except requests.exceptions.HTTPError as e:
        details = ""
        if e.response is not None:
            details = e.response.text
        return f"Błąd HTTP: {e}. Szczegóły: {details}"
    except Exception as e:
        return f"Błąd: {e}"


def main():
    print(get_purpose(file_path, language))


if __name__ == "__main__":
    main()