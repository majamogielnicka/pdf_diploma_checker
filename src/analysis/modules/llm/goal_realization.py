"""Assess whether a thesis purpose is realized using the thesis ending fragment."""

import sys
import os
import json
import time
import gc

from llama_cpp import Llama


_src_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for _p in (os.path.dirname(_src_dir), _src_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common.path import resource_path

from analysis.modules.llm.config import THESIS_PATH, LANGUAGE, MODEL_PATH, N_GPU_LAYERS
from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
from analysis.modules.llm.get_purpose import get_purpose


N_CTX = 4096
N_THREADS = None
MAX_NEW_TOKENS = 350

MAX_END_FRAGMENT_CHARS = 9000

SUPPORTED_LANGUAGES = {"pl", "en"}

_LLM = None


ENDING_HEADINGS = [
    "PODSUMOWANIE",
    "ZAKOŃCZENIE",
    "WNIOSKI KOŃCOWE",
    "WNIOSKI",
    "CONCLUSIONS",
    "CONCLUSION",
    "FINAL REMARKS",
    "SUMMARY",
]


MESSAGES = {
    "pl": {
        "unsupported_language": "Nieobsługiwany język: {language}",
        "invalid_json": "Model nie zwrócił poprawnego JSON-a.",
        "missing_text_label": "brak tekstu",
        "missing_text_reason": "Nie przekazano tekstu pracy.",
        "missing_purpose_label": "brak celu",
        "missing_purpose_reason": "Nie przekazano celu pracy.",
        "missing_ending_label": "brak zakończenia",
        "missing_ending_reason": "Nie udało się wyodrębnić końcowego fragmentu pracy.",
        "error_label": "błąd",
        "file_not_exists": "Błąd: plik nie istnieje: {path}",
        "model_not_exists": "Błąd: model nie istnieje: {path}",
        "pdf_extraction_none": "Błąd: ekstrakcja PDF zwróciła None.",
        "purpose_header": "CEL PRACY:",
        "goal_realization_header": "OCENA REALIZACJI CELU:",
        "execution_time": "Czas działania programu: {seconds:.2f} s",
        "realized": "zrealizowany",
        "partially_realized": "częściowo zrealizowany",
        "not_realized": "niezrealizowany",
    },
    "en": {
        "unsupported_language": "Unsupported language: {language}",
        "invalid_json": "The model did not return valid JSON.",
        "missing_text_label": "missing text",
        "missing_text_reason": "No thesis text was provided.",
        "missing_purpose_label": "missing purpose",
        "missing_purpose_reason": "No thesis purpose was provided.",
        "missing_ending_label": "missing ending",
        "missing_ending_reason": "Could not extract the ending fragment of the thesis.",
        "error_label": "error",
        "file_not_exists": "Error: file does not exist: {path}",
        "model_not_exists": "Error: model does not exist: {path}",
        "pdf_extraction_none": "Error: PDF extraction returned None.",
        "purpose_header": "THESIS PURPOSE:",
        "goal_realization_header": "GOAL REALIZATION ASSESSMENT:",
        "execution_time": "Program execution time: {seconds:.2f} s",
        "realized": "realized",
        "partially_realized": "partially realized",
        "not_realized": "not realized",
    },
}


SYSTEM_PROMPTS = {
    "pl": (
        "Jesteś precyzyjnym ekspertem oceniającym realizację celu pracy dyplomowej. "
        "Nie wymagaj dosłownej deklaracji realizacji celu, jeśli realizacja wynika z opisanych wyników. "
        "Zwracasz wyłącznie poprawny JSON."
    ),
    "en": (
        "You are a precise expert assessing whether a thesis purpose has been realized. "
        "Do not require an explicit statement that the purpose was achieved if realization follows from the described results. "
        "Return only valid JSON."
    ),
}


def normalize_language(language):
    """Validate and normalize language code to one of supported values."""

    language = str(language or "").lower().strip()

    if language in SUPPORTED_LANGUAGES:
        return language

    message = MESSAGES["pl"]["unsupported_language"].format(language=language)
    raise ValueError(message)


def get_message(key, language, **kwargs):
    """Return localized message text, optionally formatted with kwargs."""

    language = normalize_language(language)
    message = MESSAGES[language][key]

    if kwargs:
        return message.format(**kwargs)

    return message


def normalize_text(text):
    """Normalize whitespace and non-breaking spaces in free-form text."""

    if not text:
        return ""

    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def extract_ending_fragment(text):
    """Extract thesis ending fragment based on known final-section headings."""

    text = str(text or "")

    if not text.strip():
        return ""

    normalized = normalize_text(text)
    upper_text = normalized.upper()

    best_start = -1

    for heading in ENDING_HEADINGS:
        idx = upper_text.rfind(heading)
        if idx > best_start:
            best_start = idx

    if best_start != -1:
        fragment = normalized[best_start:]
    else:
        fragment = normalized[-MAX_END_FRAGMENT_CHARS:]

    if len(fragment) > MAX_END_FRAGMENT_CHARS:
        fragment = fragment[:MAX_END_FRAGMENT_CHARS]

    return fragment.strip()


def get_llm():
    """Return a lazily initialized singleton Llama instance."""

    global _LLM

    if _LLM is None:
        _LLM = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
            chat_format="gemma",
            verbose=False,
        )

    return _LLM


def cleanup_goal_realization_llm():
    """Release goal realization LLM instance to free RAM/VRAM."""

    global _LLM

    llm = _LLM
    _LLM = None

    if llm is not None:
        try:
            close_fn = getattr(llm, "close", None)
            if callable(close_fn):
                close_fn()
        except Exception:
            pass

        try:
            del llm
        except Exception:
            pass

    gc.collect()


def build_goal_realization_prompt(text, purpose, language):
    """Build language-specific prompt for goal realization evaluation."""

    language = normalize_language(language)
    purpose = normalize_text(purpose)
    ending_fragment = extract_ending_fragment(text)

    if language == "en":
        return f"""
Assess whether the thesis purpose was realized based on the final part of the thesis.

Rules:
- Use only the provided thesis purpose and final fragment.
- Do not require the exact phrase "the purpose was achieved".
- Treat the purpose as realized if the final fragment shows that the main planned actions from the purpose were actually completed.
- For a purpose such as "synthesis and characterization of a material", the key criterion is whether the material was obtained and characterized.
- Do not lower the score only because the final application, such as tissue regeneration, is described as potential, if the main experimental purpose was completed.
- Check whether the final fragment confirms synthesis, characterization, analysis, testing, comparison, evaluation, or interpretation corresponding to the thesis purpose.
- Give 100 if the main purpose was clearly realized through described results, even if the author does not explicitly write "the purpose was achieved".
- Give 50 only if synthesis or characterization was performed, but most other declared components are missing.
- Give 0 only if the final fragment gives no evidence that the purpose was completed.
- Return only valid JSON.
- The JSON values must be written in English.

JSON format:
{{
  "score": 100,
  "label": "realized",
  "reason": "short explanation",
  "evidence": "short fragment or paraphrase from the final part"
}}

THESIS PURPOSE:
{purpose}

FINAL FRAGMENT:
{ending_fragment}
""".strip()

    return f"""
Oceń, czy cel pracy został zrealizowany na podstawie końcowej części pracy.

Zasady:
- korzystaj wyłącznie z podanego celu pracy i końcowego fragmentu pracy
- nie wymagaj dosłownego zdania typu „cel pracy został zrealizowany”
- uznaj cel za zrealizowany, jeśli z końcowego fragmentu wynika, że wykonano główne działania zadeklarowane w celu
- dla celu typu „synteza i charakterystyka materiału” najważniejsze jest potwierdzenie, że materiał otrzymano oraz scharakteryzowano
- nie obniżaj oceny tylko dlatego, że zastosowanie końcowe, np. regeneracja tkanki miękkiej, jest opisane jako potencjalne, jeśli główny cel eksperymentalny został wykonany
- sprawdź, czy końcowy fragment potwierdza syntezę, charakterystykę, analizę, badania, porównanie, ocenę lub interpretację zgodną z celem pracy
- daj 100, jeśli główny cel został jasno zrealizowany przez opisane wyniki, nawet jeśli autor nie napisał wprost „cel został osiągnięty”
- daj 50 tylko wtedy, gdy wykonano syntezę albo charakterystykę, ale brakuje większości pozostałych elementów celu
- daj 0 tylko wtedy, gdy końcowy fragment nie daje dowodu realizacji celu
- zwróć wyłącznie poprawny JSON
- wartości w JSON-ie zapisz po polsku

Format JSON:
{{
  "score": 100,
  "label": "zrealizowany",
  "reason": "krótkie uzasadnienie",
  "evidence": "krótki fragment albo parafraza z końcowej części pracy"
}}

CEL PRACY:
{purpose}

KOŃCOWY FRAGMENT PRACY:
{ending_fragment}
""".strip()


def extract_json_from_response(response_text, language="pl"):
    """Parse JSON from model response, including wrapped JSON snippets."""

    language = normalize_language(language)
    response_text = response_text.strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError(get_message("invalid_json", language))

    return json.loads(response_text[start:end + 1])


def normalize_goal_result(data, language):
    """Normalize model output to expected score/label/reason/evidence schema."""

    language = normalize_language(language)

    score = data.get("score", 0)

    try:
        score = int(score)
    except Exception:
        score = 0

    if score not in {0, 50, 100}:
        score = 0

    label = normalize_text(data.get("label") or "")
    reason = normalize_text(data.get("reason") or "")
    evidence = normalize_text(data.get("evidence") or "")

    if not label:
        if score == 100:
            label = get_message("realized", language)
        elif score == 50:
            label = get_message("partially_realized", language)
        else:
            label = get_message("not_realized", language)

    return {
        "score": score,
        "label": label,
        "reason": reason,
        "evidence": evidence,
    }


def check_goal_realization(text, purpose, language):
    """Evaluate thesis purpose realization and return normalized structured result."""

    try:
        language = normalize_language(language)
    except Exception as e:
        return {
            "score": 0,
            "label": MESSAGES["pl"]["error_label"],
            "reason": str(e),
            "evidence": "",
        }

    text = normalize_text(text)
    purpose = normalize_text(purpose)

    if not text:
        return {
            "score": 0,
            "label": get_message("missing_text_label", language),
            "reason": get_message("missing_text_reason", language),
            "evidence": "",
        }

    if not purpose:
        return {
            "score": 0,
            "label": get_message("missing_purpose_label", language),
            "reason": get_message("missing_purpose_reason", language),
            "evidence": "",
        }

    ending_fragment = extract_ending_fragment(text)

    if not ending_fragment:
        return {
            "score": 0,
            "label": get_message("missing_ending_label", language),
            "reason": get_message("missing_ending_reason", language),
            "evidence": "",
        }

    prompt = build_goal_realization_prompt(
        text=text,
        purpose=purpose,
        language=language,
    )

    try:
        llm = get_llm()

        response = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPTS[language],
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=MAX_NEW_TOKENS,
            temperature=0.0,
            top_p=0.2,
            repeat_penalty=1.05,
        )

        response_text = response["choices"][0]["message"]["content"].strip()
        data = extract_json_from_response(response_text, language)

        return normalize_goal_result(data, language)

    except Exception as e:
        return {
            "score": 0,
            "label": get_message("error_label", language),
            "reason": str(e),
            "evidence": "",
        }

    finally:
        cleanup_goal_realization_llm()


def get_score_from_goal_result(goal_result):
    """Extract integer score from a goal realization result dictionary."""

    try:
        return int(goal_result.get("score", 0))
    except (TypeError, ValueError):
        return 0


def main():
    """Run workflow for purpose realization assessment."""

    pdf_path = THESIS_PATH

    try:
        language = normalize_language(LANGUAGE)
    except Exception as e:
        print(e)
        return

    if not pdf_path.exists():
        print(get_message("file_not_exists", language, path=pdf_path))
        return

    if not MODEL_PATH.exists():
        print(get_message("model_not_exists", language, path=MODEL_PATH))
        return

    raw_doc = extractPDF_llm(str(pdf_path.resolve()))

    if raw_doc is None:
        print(get_message("pdf_extraction_none", language))
        return

    text = get_plain_text(pdf_path)
    purpose = get_purpose(text, language)

    result = check_goal_realization(
        text=text,
        purpose=purpose,
        language=language,
    )

    print(get_message("purpose_header", language))
    print(purpose)
    print()
    print(get_message("goal_realization_header", language))
    print(json.dumps(result, ensure_ascii=False, indent=2))


def get_purpose_grade(text, purpose, language):
    """Return only numeric purpose-realization grade for pipeline usage."""

    try:
        language = normalize_language(language)
    except Exception:
        return 0

    if not MODEL_PATH.exists():
        return 0

    if text is None:
        if not THESIS_PATH.exists():
            return 0
        text = get_plain_text(THESIS_PATH)

    if purpose is None:
        purpose = get_purpose(text, language)

    result = check_goal_realization(
        text=text,
        purpose=purpose,
        language=language,
    )

    score = result.get("score", 0)

    try:
        score = int(score)
    except (ValueError, TypeError):
        return 0

    if score not in {0, 50, 100}:
        return 0

    return score


if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()

    try:
        language = normalize_language(LANGUAGE)
    except Exception:
        language = "pl"

    print(get_message("execution_time", language, seconds=end - start))