import sys
import os
import requests
from llama_cpp import Llama

_src_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for _p in (os.path.dirname(_src_dir), _src_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common.path import resource_path

from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
from analysis.modules.llm.config import MODEL_PATH, LANGUAGE, THESIS_PATH


MODEL_NAME = str(MODEL_PATH)

CHUNK_SIZE = 1400
CHUNK_OVERLAP = 200
MAX_CHUNKS = 40

N_CTX = 4096
N_THREADS = 8
N_GPU_LAYERS = -1

_IS_MAIN_SCRIPT = __name__ == "__main__"


PROMPTS = {
    "pl": {
        "find_clean": """
Przeczytaj fragment pracy i znajdź pełne zdanie, w którym autor deklaruje cel tej konkretnej pracy dyplomowej.

Zasady:
- odpowiedź tylko po polsku
- zwróć tylko wtedy, gdy w fragmencie jest jawnie zadeklarowany cel tej pracy
- zwróć pełne zdanie celu, nie sam fragment zdania
- nie wycinaj samej końcówki zdania po słowach typu „umożliwiających”, „pozwalających”, „dotyczących”
- jeśli cel zaczyna się od „Celem pracy jest...”, zwróć całe zdanie po tym sformułowaniu albo jego pełną treść
- jeśli cel zaczyna się od „Niniejsza praca koncentruje się na...”, zwróć całe zdanie po tym sformułowaniu albo jego pełną treść
- jeśli cel zawiera główny obiekt pracy, np. aplikację, system, wyszukiwarkę, metodę, model, układ, materiał lub algorytm, zachowaj ten obiekt
- zachowaj dokładnie znaczenie celu
- nie dodawaj nowych informacji
- nie streszczaj
- nie wybieraj tła teoretycznego, motywacji, opisu metody, wyniku ani wniosku
- nie kończ kropką
- jeśli nie ma jawnie zadeklarowanego celu tej pracy, zwróć dokładnie: BRAK

Fragment:
{content}
""".strip(),

        "rewrite_impersonal": """
Przeredaguj podany cel pracy do formy bezosobowej.

Zasady:
- odpowiedź tylko po polsku
- zachowaj dokładnie ten sam sens
- zachowaj główny obiekt pracy, np. aplikację, system, wyszukiwarkę, metodę, model, układ, materiał lub algorytm
- nie zamieniaj celu na ogólną korzyść typu „zapewnienie możliwości...”, jeśli w celu jest mowa o stworzeniu, opracowaniu, zaprojektowaniu lub analizie
- nie dodawaj nowych informacji
- nie usuwaj ważnych elementów celu
- usuń tylko wstęp typu:
  „Celem pracy jest”,
  „Celem niniejszej pracy jest”,
  „Niniejsza praca koncentruje się na”,
  „Praca ma na celu”
- zacznij od właściwego rzeczownika odczasownikowego, np. „stworzenie”, „opracowanie”, „zaprojektowanie”, „analiza”, „ocena”, „badanie”
- nie kończ kropką
- zwróć wyłącznie przeredagowany cel

Cel:
{purpose}
""".strip(),

        "select_best": """
Poniżej znajduje się lista kandydatów na cel pracy dyplomowej.

Zasady:
- wybierz tylko jeden, który jest rzeczywistym celem całej pracy autora
- wybierz kandydat zawierający główny obiekt pracy, np. aplikację, system, wyszukiwarkę, metodę, model, układ, materiał lub algorytm
- odrzuć zdania ogólne opisujące znaczenie tematu, motywację badań lub cele ogólne dziedziny
- odrzuć zdania opisujące wyłącznie korzyść, np. „zapewnienie możliwości...”, jeśli inny kandydat mówi o stworzeniu, opracowaniu, zaprojektowaniu lub analizie konkretnego obiektu
- wybierz kandydat, który odnosi się bezpośrednio do tej konkretnej pracy autora
- nie dodawaj nic od siebie
- nie kończ kropką
- jeśli żaden kandydat nie jest rzeczywistym celem pracy, zwróć dokładnie: BRAK

Kandydaci:
{candidates}
""".strip(),
    },

    "en": {
        "find_clean": """
Read the thesis fragment and find the full sentence in which the author declares the purpose of this specific thesis.

Rules:
- answer only in English
- return a result only if the fragment explicitly declares the purpose of this thesis
- return the full purpose sentence, not only a sentence fragment
- do not cut out only the ending after words such as “enabling”, “allowing”, or “concerning”
- if the purpose starts with “The purpose of this thesis is...”, return the full meaning after that phrase
- if the purpose starts with “This thesis focuses on...”, return the full meaning after that phrase
- if the purpose contains the main object of the thesis, e.g. application, system, search engine, method, model, setup, material, or algorithm, preserve that object
- preserve the exact meaning
- do not add new information
- do not summarize
- do not choose theoretical background, motivation, method description, result, or conclusion
- do not end with a period
- if there is no explicit thesis purpose, return exactly: NONE

Fragment:
{content}
""".strip(),

        "rewrite_impersonal": """
Rewrite the given thesis purpose into an impersonal form.

Rules:
- answer only in English
- preserve exactly the same meaning
- preserve the main object of the thesis, e.g. application, system, search engine, method, model, setup, material, or algorithm
- do not change the purpose into a general benefit such as “providing the possibility...” if the purpose is about creating, developing, designing, or analyzing something
- do not add new information
- do not remove important elements
- remove only introductory phrases such as:
  “The purpose of this thesis is”,
  “This thesis focuses on”,
  “This work aims to”
- start with an appropriate noun phrase, e.g. “creation”, “development”, “design”, “analysis”, “evaluation”, or “investigation”
- do not end with a period
- return only the rewritten purpose

Purpose:
{purpose}
""".strip(),

        "select_best": """
Below is a list of candidates for the purpose of a thesis.

Rules:
- choose only one that is the real overall purpose of the author's thesis
- choose the candidate containing the main object of the thesis, e.g. application, system, search engine, method, model, setup, material, or algorithm
- reject general statements about topic importance, research motivation, or broad field-level goals
- reject candidates describing only a general benefit if another candidate describes creating, developing, designing, or analyzing a concrete object
- choose the candidate that refers directly to this specific thesis
- do not add anything
- do not end with a period
- if none of the candidates is the real thesis purpose, return exactly: NONE

Candidates:
{candidates}
""".strip(),
    },
}


_LLAMA_MODELS = {}


def print_if_main(*args, **kwargs):
    if _IS_MAIN_SCRIPT:
        print(*args, **kwargs)


def ask_model(model_name, prompt, num_predict=120):
    if model_name not in _LLAMA_MODELS:
        _LLAMA_MODELS[model_name] = Llama(
            model_path=model_name,
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
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


def rewrite_to_impersonal_form(purpose, language):
    purpose = normalize_text(purpose)

    if not purpose:
        return ""

    prompt = build_prompt(
        "rewrite_impersonal",
        language,
        purpose=purpose,
    )

    result = normalize_output(
        ask_model(
            MODEL_NAME,
            prompt,
            num_predict=120,
        )
    )

    if not result:
        return purpose

    if is_negative_answer(result, language):
        return purpose

    return result


def collect_goal_candidates(full_text, language):
    chunks = split_into_chunks(full_text)
    candidates = []

    for chunk_index, chunk in enumerate(chunks, start=1):
        prompt = build_prompt("find_clean", language, content=chunk)

        result = normalize_output(
            ask_model(
                MODEL_NAME,
                prompt,
                num_predict=120,
            )
        )

        if is_negative_answer(result, language):
            continue

        if result:
            candidates.append(result)

            print_if_main()
            print_if_main(f"ZNALEZIONY CEL W CHUNKU {chunk_index}:")
            print_if_main(result)
            print_if_main()

            break

    return candidates


def select_best_goal(candidates, language):
    if not candidates:
        return ""

    if len(candidates) == 1:
        raw_purpose = candidates[0]

        print_if_main("CEL PRZED REWRITE:")
        print_if_main(raw_purpose)
        print_if_main()

        rewritten_purpose = rewrite_to_impersonal_form(raw_purpose, language)

        print_if_main("CEL PO REWRITE:")
        print_if_main(rewritten_purpose)
        print_if_main()

        return rewritten_purpose

    joined = "\n".join(f"- {candidate}" for candidate in candidates)
    prompt = build_prompt("select_best", language, candidates=joined)

    result = normalize_output(
        ask_model(
            MODEL_NAME,
            prompt,
            num_predict=120,
        )
    )

    if is_negative_answer(result, language):
        return ""

    print_if_main("CEL WYBRANY PRZED REWRITE:")
    print_if_main(result)
    print_if_main()

    rewritten_purpose = rewrite_to_impersonal_form(result, language)

    print_if_main("CEL PO REWRITE:")
    print_if_main(rewritten_purpose)
    print_if_main()

    return rewritten_purpose


def get_purpose(full_text, language="pl"):
    full_text = normalize_text(full_text)

    if not full_text:
        if language == "pl":
            return "Błąd: nie udało się odczytać treści pracy."
        return "Error: could not read thesis text."

    try:
        candidates = collect_goal_candidates(full_text, language)
        clean_goal = select_best_goal(candidates, language)

        if not clean_goal:
            if language == "pl":
                return "Brak jasno określonego celu pracy."
            return "No clearly defined thesis purpose found."

        return clean_goal

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
    full_text = get_plain_text(THESIS_PATH)
    result = get_purpose(full_text, LANGUAGE)

    print("WYNIK KOŃCOWY:")
    print(result)


if __name__ == "__main__":
    main()