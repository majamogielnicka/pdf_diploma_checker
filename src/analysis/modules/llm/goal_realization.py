import sys
import json
from pathlib import Path

from llama_cpp import Llama


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)


MODEL_PATH = Path.home() / "models" / "gemma2" / "gemma-2-9b-it-Q4_K_M.gguf"

N_CTX = 4096
N_THREADS = None
N_GPU_LAYERS = 0
MAX_NEW_TOKENS = 350

MAX_END_FRAGMENT_CHARS = 9000

_LLM = None

ENDING_HEADINGS = [
    "PODSUMOWANIE",
    "ZAKOŃCZENIE",
    "WNIOSKI KOŃCOWE",
    "WNIOSKI",
    "CONCLUSIONS",
    "CONCLUSION",
    "FINAL REMARKS",
]


def normalize_text(text):
    if not text:
        return ""
    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def extract_ending_fragment(text):
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


def build_goal_realization_prompt(text, purpose, language):
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


def extract_json_from_response(response_text):
    response_text = response_text.strip()

    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    start = response_text.find("{")
    end = response_text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model nie zwrócił poprawnego JSON-a.")

    return json.loads(response_text[start:end + 1])


def normalize_goal_result(data, language):
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
        if language == "en":
            label = {
                100: "realized",
                50: "partially realized",
                0: "not realized",
            }[score]
        else:
            label = {
                100: "zrealizowany",
                50: "częściowo zrealizowany",
                0: "niezrealizowany",
            }[score]

    return {
        "score": score,
        "label": label,
        "reason": reason,
        "evidence": evidence,
    }


def check_goal_realization(text, purpose, language="pl"):
    text = normalize_text(text)
    purpose = normalize_text(purpose)

    if not text:
        return {
            "score": 0,
            "label": "brak tekstu" if language == "pl" else "missing text",
            "reason": "Nie przekazano tekstu pracy." if language == "pl" else "No thesis text was provided.",
            "evidence": "",
        }

    if not purpose:
        return {
            "score": 0,
            "label": "brak celu" if language == "pl" else "missing purpose",
            "reason": "Nie przekazano celu pracy." if language == "pl" else "No thesis purpose was provided.",
            "evidence": "",
        }

    ending_fragment = extract_ending_fragment(text)

    if not ending_fragment:
        return {
            "score": 0,
            "label": "brak zakończenia" if language == "pl" else "missing ending",
            "reason": "Nie udało się wyodrębnić końcowego fragmentu pracy." if language == "pl" else "Could not extract the ending fragment.",
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
                    "content": (
                        "Jesteś precyzyjnym ekspertem oceniającym realizację celu pracy dyplomowej. "
                        "Nie wymagaj dosłownej deklaracji realizacji celu, jeśli realizacja wynika z opisanych wyników. "
                        "Zwracasz wyłącznie poprawny JSON."
                    ),
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
        data = extract_json_from_response(response_text)

        return normalize_goal_result(data, language)

    except Exception as e:
        return {
            "score": 0,
            "label": "błąd" if language == "pl" else "error",
            "reason": str(e),
            "evidence": "",
        }


def main():
    from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
    from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
    from analysis.modules.llm.get_purpose import get_purpose

    pdf_path = PROJECT_ROOT / "data" / "jago.pdf"
    language = "pl"

    if not pdf_path.exists():
        print(f"Błąd: plik nie istnieje: {pdf_path}")
        return

    if not MODEL_PATH.exists():
        print(f"Błąd: model nie istnieje: {MODEL_PATH}")
        return

    raw_doc = extractPDF_llm(str(pdf_path.resolve()))

    if raw_doc is None:
        print("Błąd: ekstrakcja PDF zwróciła None.")
        return

    text = get_plain_text(pdf_path)
    purpose = get_purpose(text, language)

    result = check_goal_realization(
        text=text,
        purpose=purpose,
        language=language,
    )

    print("CEL PRACY:")
    print(purpose)
    print()
    print("OCENA REALIZACJI CELU:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()