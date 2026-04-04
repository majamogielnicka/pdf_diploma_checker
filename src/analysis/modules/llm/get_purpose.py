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


file_path = PROJECT_ROOT / "data" / "inż_1_.pdf"
language = "pl"

MODEL_PL = "bielik-11b-v3-q4km:latest"
MODEL_EN = "qwen2.5:latest"

OUTPUT_DIR = BASE_DIR / "wyniki"


def ask_ollama(prompt, model, num_predict=60):
    model = model.strip()

    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "15m",
            "options": {
                "temperature": 0.0,
                "num_predict": num_predict,
                "top_p": 0.2,
                "num_ctx": 4096,
            },
        },
        timeout=600,
    )

    if not resp.ok:
        raise requests.exceptions.HTTPError(
            f"{resp.status_code}: {resp.text}",
            response=resp,
        )

    data = resp.json()
    return data.get("response", "").strip()


def prepare_text(path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_text = get_plain_text(path)
    plain_text_path = OUTPUT_DIR / f"{path.stem}_plain_text.txt"
    plain_text_path.write_text(raw_text, encoding="utf-8")
    return " ".join(raw_text.split()).strip()


def split_into_chunks(text, chunk_size=2000, max_chunks=20):
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
- jeśli da się ustalić cel, zwróć wyłącznie jedną krótką frazę rzeczownikową
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
Read the thesis fragment and decide whether the main purpose of the thesis can be determined from it.

Look especially for explicit purpose statements in the introduction, abstract, or passages describing the author's intention.

Rules:
- answer only in English
- if the thesis purpose can be determined from this fragment, return exactly one sentence
- if it cannot be determined reliably from this fragment, return exactly: NONE
- do not summarize the text
- do not quote literally
- do not create a list
- do not add commentary
- the answer should be factual, impersonal, and not start with phrases such as "The purpose of this thesis is" or "This thesis aims to"

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
Based on the candidates below, choose the single best formulation of the thesis purpose.

Rules:
- answer only in English
- return exactly one sentence
- choose only one best purpose
- do not create a list
- do not comment
- do not add information beyond the candidates
- the answer should be factual, impersonal, and not start with phrases such as "The purpose of this thesis is" or "This thesis aims to"

Candidates:
{joined}
""".strip()


def normalize_candidate(text):
    return " ".join(text.split()).strip()


def collect_purpose_candidates(text, language="pl"):
    chunks = split_into_chunks(text)
    candidates = []

    for chunk in chunks:
        if language == "pl":
            prompt = build_candidate_prompt_pl(chunk)
            result = ask_ollama(prompt, MODEL_PL, num_predict=60)
            result = normalize_candidate(result)
            if result and result != "BRAK":
                candidates.append(result)
        else:
            prompt = build_candidate_prompt_en(chunk)
            result = ask_ollama(prompt, MODEL_EN, num_predict=60)
            result = normalize_candidate(result)
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
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {file_path}")

    full_text = prepare_text(file_path)

    if not full_text:
        return "Błąd: nie udało się odczytać treści pracy."

    try:
        candidates = collect_purpose_candidates(full_text, language=language)

        if not candidates:
            if language == "pl":
                return "Brak jasno określonego celu pracy."
            return "No clearly defined thesis purpose found."

        if len(candidates) == 1:
            return candidates[0]

        if language == "pl":
            final_prompt = build_final_prompt_pl(candidates)
            return normalize_candidate(ask_ollama(final_prompt, MODEL_PL, num_predict=60))
        elif language == "en":
            final_prompt = build_final_prompt_en(candidates)
            return normalize_candidate(ask_ollama(final_prompt, MODEL_EN, num_predict=60))
        else:
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