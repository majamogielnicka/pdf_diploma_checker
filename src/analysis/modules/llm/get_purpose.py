import sys
from pathlib import Path
import requests

file_path = "src/theses/kana.pdf"

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
REDACTION_DIR = SRC_DIR / "redaction"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(REDACTION_DIR))

from redaction.converter_linguistics import get_plain_text

#MODEL_PL = "SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M"
MODEL_PL = "SpeakLeash/bielik-7b-instruct-v0.1-gguf:latest" 
MODEL_EN = "qwen2.5:14b"

OUTPUT_DIR = BASE_DIR / "wyniki"
PLAIN_TEXT_PATH = OUTPUT_DIR / "plain_text.txt"

PROMPT_PL = """
Przeczytaj fragment pracy dyplomowej i wyodrębnij główny cel pracy.

Zasady:
- odpowiedź wyłącznie po polsku
- zwróć wyłącznie jedno zdanie
- nie streszczaj całej pracy
- nie twórz listy
- nie cytuj dosłownie, chyba że to konieczne do zachowania sensu
- jeśli w tekście da się znaleźć jasno sformułowany cel pracy, zwróć go własnymi słowami
- jeśli nie ma jasno sformułowanego celu, ale jest streszczenie lub abstract, wywnioskuj cel z tego fragmentu
- jeśli nie da się wiarygodnie ustalić celu pracy, zwróć dokładnie: Brak jasno określonego celu pracy.
- forma rzeczowa i bezosobowa
- najlepiej zacznij od: "Celem pracy jest..." albo "Praca ma na celu..."

Tekst:
{content}
"""

PROMPT_EN = """
Read the thesis text and extract the main purpose of the thesis.

Rules:
- answer only in English
- return exactly one sentence
- do not summarize the whole thesis
- do not create a list
- do not quote literally unless necessary
- if the thesis contains a clearly stated purpose, restate it in your own words
- if there is no clearly stated purpose but there is an abstract, infer the purpose from it
- if the purpose cannot be determined reliably, return exactly: No clearly defined thesis purpose found.
- use a factual and impersonal style
- preferably start with: "The purpose of this thesis is..." or "This thesis aims to..."

Text:
{content}
"""


def ask_ollama(prompt: str, model: str) -> str:
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 200,
                "top_p": 0.3
            }
        },
        timeout=600
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def prepare_text(path: Path) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw_text = get_plain_text(path)
    PLAIN_TEXT_PATH.write_text(raw_text, encoding="utf-8")

    clean_text = " ".join(raw_text.split())
    return clean_text


def truncate_text(text: str, max_chars: int = 20000) -> str:
    return text[:max_chars].strip()


def get_purpose(path, language="pl"):
    path = Path(path)

    if not path.exists():
        return "Błąd: nie znaleziono pliku."

    try:
        text = prepare_text(path)
    except Exception as e:
        return f"Błąd podczas odczytu tekstu pracy: {e}"

    if not text:
        return "Błąd: nie udało się odczytać treści pracy."

    truncated_text = truncate_text(text)

    if language == "pl":
        model = MODEL_PL
        prompt = PROMPT_PL.format(content=truncated_text)
        fallback = "Brak jasno określonego celu pracy."
    elif language == "en":
        model = MODEL_EN
        prompt = PROMPT_EN.format(content=truncated_text)
        fallback = "No clearly defined thesis purpose found."
    else:
        return "Błąd: nieobsługiwany język."

    try:
        result = ask_ollama(prompt, model)
        return result if result else fallback
    except requests.exceptions.ReadTimeout:
        return "Błąd: model nie odpowiedział na czas."
    except requests.exceptions.ConnectionError:
        return "Błąd: nie udało się połączyć z Ollamą."
    except requests.exceptions.HTTPError as e:
        return f"Błąd HTTP: {e}"
    except Exception as e:
        return f"Błąd: {e}"


def main():
    path = Path(file_path)
    language = "pl"
    print(get_purpose(path, language))


if __name__ == "__main__":
    main()