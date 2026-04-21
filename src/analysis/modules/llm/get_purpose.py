import sys
from pathlib import Path
import requests
from llama_cpp import Llama

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

MODEL_PATH = Path.home() / "models" / "gemma2" / "gemma-2-9b-it-Q4_K_M.gguf"
MODEL_NAME = str(MODEL_PATH)

OUTPUT_DIR = BASE_DIR / "wyniki"
REQUEST_TIMEOUT = 600

CHUNK_SIZE = 1400
CHUNK_OVERLAP = 200
MAX_CHUNKS = 45

PROMPTS = {
    "pl": {
        "find_clean": """
Przeczytaj fragment pracy i sprawdź, czy autor jawnie deklaruje cel tej konkretnej pracy dyplomowej.

Zasady:
- odpowiedź tylko po polsku
- zwróć wynik tylko wtedy, gdy autor wprost deklaruje cel tej pracy
- chodzi wyłącznie o jawnie zadeklarowany cel pracy autora, a nie o tematykę, motywację, znaczenie dziedziny, przewagi materiału, tło teoretyczne, opis problemu, metodę, wynik ani wniosek
- nie wybieraj zdań ogólnych typu: że coś jest ważne, stanowi alternatywę, budzi zainteresowanie, ma szerokie zastosowanie, jest perspektywiczne, pozostaje istotne, pozwala lepiej zrozumieć itp.
- jeśli w fragmencie jest jawnie zadeklarowany cel pracy, zwróć go od razu w czystej, bezosobowej formie
- zachowaj dokładnie znaczenie
- nie dodawaj nowych informacji
- nie skracaj celu, jeśli zawiera kilka ważnych elementów
- usuń formy typu "Celem pracy jest", "Celem niniejszej pracy była", ale zachowaj sens
- nie kończ kropką
- jeśli nie ma wprost zadeklarowanego celu tej pracy, zwróć dokładnie: BRAK

Fragment:
{content}
""".strip(),
        "select_best": """
Poniżej znajduje się lista kandydatów na cel pracy dyplomowej.

Zasady:
- wybierz tylko jeden, który jest rzeczywistym celem całej pracy autora
- odrzuć zdania ogólne opisujące znaczenie tematu, motywację badań lub cele ogólne dziedziny
- odrzuć zdania opisujące co "warto zbadać", "lepiej zrozumieć", "istotne jest", "stanowi alternatywę", "jest perspektywiczne"
- wybierz kandydat, który odnosi się bezpośrednio do tej konkretnej pracy autora
- preferuj kandydat zawierający informację o badanym materiale/obiekcie i czynności badawczej, np. synteza, charakterystyka, analiza, ocena, badanie
- zwróć wynik w formie bezosobowej
- nie dodawaj nic od siebie
- nie kończ kropką
- jeśli żaden kandydat nie jest rzeczywistym celem pracy, zwróć dokładnie: BRAK

Kandydaci:
{candidates}
""".strip(),
    },
    "en": {
        "find_clean": """
Read the thesis fragment and determine whether the author explicitly states the purpose of this specific thesis.

Rules:
- answer only in English
- return a result only if the author explicitly states the purpose of this thesis
- look only for the explicitly declared thesis purpose, not for topic importance, motivation, background, material advantages, methods, results, or conclusions
- do not choose general sentences saying something is important, promising, widely used, attractive, functional, or helps better understand a phenomenon
- if the fragment contains an explicitly declared thesis purpose, return it directly in a clean impersonal form
- preserve the exact meaning
- do not add new information
- do not shorten the purpose if it contains several important elements
- remove phrases like "The purpose of this thesis is" while preserving meaning
- do not end with a period
- if there is no explicitly declared thesis purpose, return exactly: NONE

Fragment:
{content}
""".strip(),
        "select_best": """
Below is a list of candidates for the purpose of a thesis.

Rules:
- choose only one that is the real overall purpose of the author's thesis
- reject general statements about topic importance, research motivation, or broad field-level goals
- reject statements like "it is important", "it helps better understand", "it is a functional alternative", "it is promising"
- choose the candidate that refers directly to this specific thesis
- prefer a candidate that contains the studied material/object and the research action, e.g. synthesis, characterization, analysis, evaluation, investigation
- return the result in impersonal form
- do not add anything
- do not end with a period
- if none of the candidates is the real thesis purpose, return exactly: NONE

Candidates:
{candidates}
""".strip(),
    },
}

_LLAMA_MODELS = {}


def ask_model(model_name, prompt, num_predict=120):
    if model_name not in _LLAMA_MODELS:
        _LLAMA_MODELS[model_name] = Llama(
            model_path=model_name,
            n_ctx=4096,
            chat_format="gemma",
            verbose=False,
        )

    llm = _LLAMA_MODELS[model_name]

    resp = llm.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "Jesteś precyzyjnym asystentem ekstrakcji informacji z prac dyplomowych. "
                    "Zwracasz wyłącznie odpowiedź zgodną z poleceniem. "
                    "Nie streszczasz, nie dopowiadasz i nie zgadujesz."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=num_predict,
        temperature=0.0,
        top_p=0.2,
        repeat_penalty=1.05,
    )

    return resp["choices"][0]["message"]["content"].strip()


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

    if text.endswith("."):
        text = text[:-1].strip()

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


def collect_goal_candidates(full_text, language):
    chunks = split_into_chunks(full_text)
    candidates = []

    for chunk in chunks:
        prompt = build_prompt("find_clean", language, content=chunk)
        result = normalize_output(ask_model(MODEL_NAME, prompt, num_predict=120))

        if is_negative_answer(result, language):
            continue

        if result not in candidates:
            candidates.append(result)

    return candidates


def select_best_goal(candidates, language):
    if not candidates:
        return ""

    joined = "\n".join(f"- {candidate}" for candidate in candidates)
    prompt = build_prompt("select_best", language, candidates=joined)
    result = normalize_output(ask_model(MODEL_NAME, prompt, num_predict=120))

    if is_negative_answer(result, language):
        return ""

    return result


def get_purpose(path, language="pl", save_artifacts=False):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

    full_text = prepare_text(path, save_plain_text=save_artifacts)

    if not full_text:
        return "Błąd: nie udało się odczytać treści pracy." if language == "pl" else "Error: could not read thesis text."

    try:
        candidates = collect_goal_candidates(full_text, language)
        clean_goal = select_best_goal(candidates, language)

        if save_artifacts:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            (OUTPUT_DIR / f"{path.stem}_goal_candidates.txt").write_text(
                "\n".join(candidates) if candidates else "[BRAK KANDYDATÓW]",
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
        return "Błąd: nie udało się połączyć z modelem." if language == "pl" else "Error: could not connect to model."
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