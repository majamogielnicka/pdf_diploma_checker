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

from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
from analysis.modules.llm.config import MODEL_PATH, THESIS_PATH


FILE_PATH = THESIS_PATH
LANGUAGE = "pl"

MODEL_NAME = str(MODEL_PATH)

CHUNK_SIZE = 1800
CHUNK_OVERLAP = 200
MAX_CHUNKS = 20

GOAL_CONTEXT_CHARS = 5000

_LLAMA_MODELS = {}


PROMPTS = {
    "pl": {
        "extract_from_goal_section": """
Przeczytaj fragment pracy dyplomowej i wyciągnij główny cel pracy.

Najważniejsze zasady:
- odpowiedz tylko po polsku
- korzystaj wyłącznie z podanego fragmentu
- fragment pochodzi z okolicy sekcji „Cel pracy”, więc szukaj celu właśnie tam
- zwróć główny cel całej pracy autora
- nie wybieraj definicji, opisu metody, tła teoretycznego ani opisu algorytmu
- nie wybieraj celu metody AHP, rynku nieruchomości, Smart City ani innego rozdziału teoretycznego
- jeśli jest zdanie typu „Niniejsza praca koncentruje się na...”, potraktuj je jako cel pracy
- jeśli jest zdanie typu „Celem pracy jest...”, potraktuj je jako cel pracy
- usuń początek typu „Celem pracy jest”, „Niniejsza praca koncentruje się na”
- zachowaj sens celu
- nie dopisuj niczego spoza fragmentu
- nie streszczaj całej pracy
- nie zwracaj listy
- nie kończ kropką
- jeśli wprost nie ma celu pracy, zwróć dokładnie: BRAK

Fragment:
{content}
""".strip(),

        "extract_from_general_chunk": """
Przeczytaj fragment pracy dyplomowej i sprawdź, czy autor jawnie deklaruje główny cel tej pracy.

Zasady:
- odpowiedz tylko po polsku
- zwróć wynik tylko wtedy, gdy w fragmencie autor jawnie deklaruje cel własnej pracy
- nie wybieraj definicji, tła teoretycznego, opisu metody, opisu algorytmu, motywacji ani wniosku
- nie wybieraj zdań o tym, co umożliwia algorytm lub metoda
- szukaj zdań typu „Celem pracy jest...” albo „Niniejsza praca koncentruje się na...”
- usuń początek typu „Celem pracy jest”, „Niniejsza praca koncentruje się na”
- zachowaj sens celu
- nie dodawaj nowych informacji
- nie zwracaj listy
- nie kończ kropką
- jeśli nie ma jawnego celu pracy, zwróć dokładnie: BRAK

Fragment:
{content}
""".strip(),

        "select_best": """
Poniżej znajduje się lista kandydatów na cel pracy dyplomowej.

Wybierz jeden prawdziwy, główny cel pracy autora.

Zasady:
- odpowiedz tylko po polsku
- wybierz cel dotyczący całej pracy, nie pojedynczego rozdziału
- jeśli jeden kandydat mówi o stworzeniu aplikacji, systemu, wyszukiwarki lub narzędzia, wybierz go
- nie wybieraj kandydata opisującego tylko metodę AHP, algorytm, teorię albo efekt działania metody
- nie łącz kandydatów
- nie dopisuj niczego od siebie
- nie kończ kropką
- jeśli żaden kandydat nie jest celem pracy, zwróć dokładnie: BRAK

Kandydaci:
{candidates}
""".strip(),
    },

    "en": {
        "extract_from_goal_section": """
Read the thesis fragment and extract the main purpose of the thesis.

Rules:
- answer only in English
- use only the provided fragment
- the fragment comes from the area around the thesis purpose section
- return the main purpose of the whole thesis
- do not choose definitions, theoretical background, method descriptions, algorithm descriptions, or conclusions
- if there is a sentence like “This thesis focuses on...”, treat it as the thesis purpose
- if there is a sentence like “The purpose of this thesis is...”, treat it as the thesis purpose
- remove introductory phrases such as “The purpose of this thesis is” while preserving the meaning
- do not add information
- do not output a list
- do not end with a period
- if there is no explicit purpose, return exactly: NONE

Fragment:
{content}
""".strip(),

        "extract_from_general_chunk": """
Read the thesis fragment and check whether the author explicitly declares the main purpose of this thesis.

Rules:
- answer only in English
- return a result only if the fragment explicitly states the purpose of this thesis
- do not choose definitions, theoretical background, method descriptions, algorithm descriptions, motivation, or conclusions
- do not choose sentences about what an algorithm or method enables
- look for sentences such as “The purpose of this thesis is...” or “This thesis focuses on...”
- remove introductory phrases while preserving meaning
- do not add information
- do not output a list
- do not end with a period
- if there is no explicit thesis purpose, return exactly: NONE

Fragment:
{content}
""".strip(),

        "select_best": """
Below is a list of candidates for the thesis purpose.

Choose one true main purpose of the author's thesis.

Rules:
- answer only in English
- choose the purpose of the whole thesis, not a single section
- if one candidate mentions creating an application, system, search engine, or tool, choose it
- do not choose a candidate describing only AHP, an algorithm, theory, or the effect of a method
- do not combine candidates
- do not add anything
- do not end with a period
- if none is the real thesis purpose, return exactly: NONE

Candidates:
{candidates}
""".strip(),
    },
}


def ask_model(model_name, prompt, num_predict=140):
    if model_name not in _LLAMA_MODELS:
        _LLAMA_MODELS[model_name] = Llama(
            model_path=model_name,
            n_ctx=4096,
            chat_format="gemma",
            verbose=False,
        )

    llm = _LLAMA_MODELS[model_name]

    response = llm.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "Jesteś precyzyjnym asystentem do ekstrakcji celu pracy dyplomowej. "
                    "Masz wyciągnąć wyłącznie główny cel pracy autora. "
                    "Nie zgadujesz, nie streszczasz i nie wybierasz teorii zamiast celu pracy."
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

    return response["choices"][0]["message"]["content"].strip()


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


def is_negative_answer(text, language):
    text = normalize_text(text).upper()
    return text == ("BRAK" if language == "pl" else "NONE")


def build_prompt(kind, language, **kwargs):
    return PROMPTS[language][kind].format(**kwargs).strip()


def find_first_existing_marker(text_upper, markers):
    best_index = -1
    best_marker = ""

    for marker in markers:
        marker_upper = marker.upper()
        index = text_upper.find(marker_upper)

        if index != -1:
            if best_index == -1 or index < best_index:
                best_index = index
                best_marker = marker

    return best_index, best_marker


def extract_goal_section_context(text, max_chars=GOAL_CONTEXT_CHARS):
    text = normalize_text(text)

    if not text:
        return ""

    text_upper = text.upper()

    goal_markers = [
        "CEL PRACY",
        "WSTĘP I CEL PRACY",
        "CEL I ZAKRES PRACY",
        "CEL NINIEJSZEJ PRACY",
        "CEL PROJEKTU",
        "CEL BADAŃ",
        "AIM OF THE THESIS",
        "PURPOSE OF THE THESIS",
        "THESIS PURPOSE",
        "OBJECTIVE OF THE THESIS",
        "AIM AND SCOPE",
    ]

    start_index, marker = find_first_existing_marker(text_upper, goal_markers)

    if start_index == -1:
        return ""

    context_start = start_index

    possible_next_markers = [
        "1.2 ",
        "1.3 ",
        "2. ",
        "2.1 ",
        "ROZDZIAŁ 2",
        "PRZEGLĄD LITERATURY",
        "STRUKTURA PRACY",
        "ZAKRES PRACY",
        "MATERIAŁY I METODY",
        "IMPLEMENTACJA",
        "LITERATURE REVIEW",
        "MATERIALS AND METHODS",
    ]

    search_from = start_index + len(marker)
    best_end = -1

    for next_marker in possible_next_markers:
        next_index = text_upper.find(next_marker.upper(), search_from)

        if next_index != -1:
            if best_end == -1 or next_index < best_end:
                best_end = next_index

    if best_end != -1 and best_end > context_start:
        context = text[context_start:best_end]
    else:
        context = text[context_start:context_start + max_chars]

    return normalize_text(context)


def split_into_chunks(
    text,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP,
    max_chunks=MAX_CHUNKS,
):
    text = normalize_text(text)

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text) and len(chunks) < max_chunks:
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]

        if end < len(text):
            last_dot = chunk.rfind(". ")
            last_question = chunk.rfind("? ")
            last_exclamation = chunk.rfind("! ")
            boundary = max(last_dot, last_question, last_exclamation)

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
    full_text = normalize_text(full_text)
    candidates = []

    goal_context = extract_goal_section_context(full_text)

    if goal_context:
        prompt = build_prompt(
            "extract_from_goal_section",
            language,
            content=goal_context,
        )

        result = normalize_output(
            ask_model(MODEL_NAME, prompt, num_predict=160)
        )

        if result and not is_negative_answer(result, language):
            candidates.append(result)

        return candidates

    chunks = split_into_chunks(full_text)

    for chunk in chunks:
        prompt = build_prompt(
            "extract_from_general_chunk",
            language,
            content=chunk,
        )

        result = normalize_output(
            ask_model(MODEL_NAME, prompt, num_predict=140)
        )

        if result and not is_negative_answer(result, language):
            if result not in candidates:
                candidates.append(result)

    return candidates


def select_best_goal(candidates, language):
    if not candidates:
        return ""

    if len(candidates) == 1:
        return candidates[0]

    joined = "\n".join(f"- {candidate}" for candidate in candidates)

    prompt = build_prompt(
        "select_best",
        language,
        candidates=joined,
    )

    result = normalize_output(
        ask_model(MODEL_NAME, prompt, num_predict=100)
    )

    if is_negative_answer(result, language):
        return ""

    if result in candidates:
        return result

    for candidate in candidates:
        if candidate in result:
            return candidate

    return result


def get_purpose(full_text, language="pl"):
    full_text = normalize_text(full_text)

    if not full_text:
        if language == "pl":
            return "Błąd: nie udało się odczytać treści pracy."
        return "Error: could not read thesis text."

    try:
        candidates = collect_goal_candidates(full_text, language)
        purpose = select_best_goal(candidates, language)

        if not purpose:
            if language == "pl":
                return "Brak jasno określonego celu pracy."
            return "No clearly defined thesis purpose found."

        return purpose

    except requests.exceptions.ReadTimeout:
        if language == "pl":
            return "Błąd: model nie odpowiedział na czas."
        return "Error: model response timed out."

    except requests.exceptions.ConnectionError:
        if language == "pl":
            return "Błąd: nie udało się połączyć z modelem."
        return "Error: could not connect to model."

    except requests.exceptions.HTTPError as e:
        details = e.response.text if e.response is not None else ""

        if language == "pl":
            return f"Błąd HTTP: {e}. Szczegóły: {details}"
        return f"HTTP error: {e}. Details: {details}"

    except Exception as e:
        if language == "pl":
            return f"Błąd: {e}"
        return f"Error: {e}"


def main():
    full_text = get_plain_text(FILE_PATH)
    result = get_purpose(full_text, LANGUAGE)
    print(result)


if __name__ == "__main__":
    main()