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

FILE_PATH = PROJECT_ROOT / "data" / "bosh.pdf"
LANGUAGE = "pl"

FIND_MODEL = "qwen2.5:latest"
REWRITE_MODEL = "qwen2.5:latest"

OUTPUT_DIR = BASE_DIR / "wyniki"
REQUEST_TIMEOUT = 600

CHUNK_SIZE = 2200
CHUNK_OVERLAP = 900
MAX_CHUNKS = 60

PROMPTS = {
    "pl": {
        "find": """
Przeczytaj fragment pracy i sprawdź, czy autor jawnie opisuje w nim główny zamiar całej pracy.

Zasady:
- odpowiedź tylko po polsku
- jeśli fragment zawiera zdanie autora opisujące główny cel całej pracy, zwróć tylko to jedno zdanie
- preferuj polską wersję, jeśli w tekście występuje także wersja angielska
- wybierz cel główny całej pracy, a nie sam etap badania, metodę, wynik ani cel szczegółowy
- możesz minimalnie uporządkować połamane spacje i łamania wierszy, ale nie zmieniaj sensu
- nie streszczaj
- nie dopowiadaj
- jeśli nie masz pewności albo w fragmencie nie ma takiego zdania, zwróć dokładnie: BRAK

Fragment:
{content}
""".strip(),
        "rewrite": """
Przeredaguj poniższe zdanie autora do czystej, bezosobowej formy samego celu pracy.

Zasady:
- odpowiedź tylko po polsku
- zwróć tylko sam cel
- zachowaj dokładnie znaczenie zdania autora
- nie usuwaj istotnych informacji
- nie skracaj celu, jeśli zawiera kilka ważnych elementów
- nie dodawaj nowych informacji
- zmień formę tak, aby zniknęła forma osobowa typu "Celem pracy jest", ale sens pozostał identyczny
- wynik ma być zwartą frazą dobrą do porównywania embeddingów
- nie kończ kropką

Zdanie autora:
{goal}
""".strip(),
    },
    "en": {
        "find": """
Read the thesis fragment and determine whether the author explicitly states the main overall purpose of the thesis.

Rules:
- answer only in English
- if the fragment contains an author sentence describing the main overall thesis purpose, return only that one sentence
- choose the overall thesis purpose, not just a sub-goal, method, or result
- you may minimally clean broken spacing and line breaks, but do not change the meaning
- do not summarize
- do not add information
- if you are not sure or there is no such sentence, return exactly: NONE

Fragment:
{content}
""".strip(),
        "rewrite": """
Rewrite the sentence below into a clean impersonal form containing only the thesis purpose.

Rules:
- answer only in English
- return only the purpose itself
- preserve the exact meaning
- do not remove essential information
- do not shorten the purpose if it contains several important parts
- do not add new information
- rewrite it so that personal wording like "The purpose of this thesis is" disappears while the meaning stays identical
- make it a compact phrase suitable for embedding comparison
- do not end with a period

Author sentence:
{goal}
""".strip(),
    },
}


def ask_ollama(model_name, prompt, num_predict=120):
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "15m",
            "options": {
                "temperature": 0.0,
                "top_p": 0.2,
                "num_predict": num_predict,
                "num_ctx": 4096,
                "repeat_penalty": 1.05,
            },
        },
        timeout=REQUEST_TIMEOUT,
    )

    if not resp.ok:
        raise requests.exceptions.HTTPError(
            f"{resp.status_code}: {resp.text}",
            response=resp,
        )

    return resp.json().get("response", "").strip()


def normalize_text(text):
    if not text:
        return ""
    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def normalize_output(text):
    text = normalize_text(text)

    if not text:
        return ""

    while text.startswith("-"):
        text = text[1:].strip()
    while text.startswith("•"):
        text = text[1:].strip()

    if text.startswith('"') and text.endswith('"') and len(text) > 1:
        text = text[1:-1].strip()

    if text.startswith("'") and text.endswith("'") and len(text) > 1:
        text = text[1:-1].strip()

    return text


def build_prompt(kind, language, **kwargs):
    return PROMPTS[language][kind].format(**kwargs).strip()


def is_negative_answer(text, language):
    text = normalize_text(text).upper()
    return text == ("BRAK" if language == "pl" else "NONE")


def prepare_text(path, save_plain_text=False):
    raw_text = get_plain_text(path)
    plain_text = normalize_text(raw_text)

    if save_plain_text:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / f"{path.stem}_plain_text.txt").write_text(plain_text, encoding="utf-8")

    return plain_text


def split_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP, max_chunks=MAX_CHUNKS):
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text) and len(chunks) < max_chunks:
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]

        if end < len(text):
            last_dot = chunk.rfind(". ")
            last_q = chunk.rfind("? ")
            last_exc = chunk.rfind("! ")
            boundary = max(last_dot, last_q, last_exc)

            if boundary > int(chunk_size * 0.45):
                chunk = chunk[:boundary + 1]
                end = start + boundary + 1

        chunk = normalize_text(chunk)
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def find_first_goal_sentence(full_text, language):
    chunks = split_into_chunks(full_text)

    for chunk in chunks:
        prompt = build_prompt("find", language, content=chunk)
        result = normalize_output(ask_ollama(FIND_MODEL, prompt, num_predict=100))

        if is_negative_answer(result, language):
            continue

        return result

    return ""


def rewrite_goal(goal_sentence, language):
    if not goal_sentence:
        return ""

    prompt = build_prompt("rewrite", language, goal=goal_sentence)
    result = normalize_output(ask_ollama(REWRITE_MODEL, prompt, num_predict=120))

    if is_negative_answer(result, language):
        return ""

    if result.endswith("."):
        result = result[:-1].strip()

    return result


def get_purpose(path, language="pl", save_artifacts=False):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

    full_text = prepare_text(path, save_plain_text=save_artifacts)

    if not full_text:
        return "Błąd: nie udało się odczytać treści pracy." if language == "pl" else "Error: could not read thesis text."

    try:
        explicit_goal = find_first_goal_sentence(full_text, language)
        clean_goal = rewrite_goal(explicit_goal, language)

        if save_artifacts:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            (OUTPUT_DIR / f"{path.stem}_goal_explicit.txt").write_text(
                explicit_goal if explicit_goal else "[BRAK CELU JAWNEGO]",
                encoding="utf-8",
            )
            (OUTPUT_DIR / f"{path.stem}_goal_clean.txt").write_text(
                clean_goal if clean_goal else "[BRAK CELU CZYSTEGO]",
                encoding="utf-8",
            )

        if not clean_goal:
            return "Brak jasno określonego celu pracy." if language == "pl" else "No clearly defined thesis purpose found."

        return clean_goal

    except requests.exceptions.ReadTimeout:
        return "Błąd: model nie odpowiedział na czas." if language == "pl" else "Error: model response timed out."
    except requests.exceptions.ConnectionError:
        return "Błąd: nie udało się połączyć z Ollamą." if language == "pl" else "Error: could not connect to Ollama."
    except requests.exceptions.HTTPError as e:
        details = e.response.text if e.response is not None else ""
        return f"Błąd HTTP: {e}. Szczegóły: {details}" if language == "pl" else f"HTTP error: {e}. Details: {details}"
    except Exception as e:
        return f"Błąd: {e}" if language == "pl" else f"Error: {e}"


def main():
    result = get_purpose(FILE_PATH, LANGUAGE, save_artifacts=True)
    print(result)


if __name__ == "__main__":
    main()