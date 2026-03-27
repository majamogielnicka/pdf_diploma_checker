import requests
from pathlib import Path
from get_subtitles import extract_subtitles_from_pdf
import sys

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

pdf_path = SRC_DIR / "theses" / "zusz.pdf"

MODEL_PL = "SpeakLeash/bielik-7b-instruct-v0.1-gguf:latest"
MODEL_EN = "qwen2.5:latest"

prompt_pl = """Streść poniższy fragment pracy dyplomowej w dokładnie jednym zdaniu.

Zasady:
- odpowiedź tylko po polsku
- zwróć tylko jedno zdanie
- nie powtarzaj polecenia
- nie przepisuj słowa „Wymagania” ani „Fragment”
- nie używaj wypunktowań
- nie cytuj
- nie dodawaj informacji spoza tekstu
- jeśli fragment jest urwany lub niepełny, streść tylko to, co wynika z treści

Tekst do streszczenia:
"""

PROMPT_EN = """Summarize the following fragment in one sentence.
Requirements:
- answer only in English
- max 1 sentence
- no quotes and no bullet points
- preserve the meaning and do not add information not present in the fragment
Fragment:
"""


def get_summary(fragment, model, prompt):
    full_prompt = prompt + fragment

    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.2,
                "num_predict": 120
            }
        }
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def get_summaries(subtitles, language):
    if language == "pl":
        model = MODEL_PL
        prompt = PROMPT_PL
    elif language == "en":
        model = MODEL_EN
        prompt = PROMPT_EN
    else:
        raise ValueError("Nieobsługiwany język")

    summaries = []

    for i, sub in enumerate(subtitles, start=1):
        content = sub["content"].strip()
        if not content:
            continue

        summary = get_summary(content, model, prompt)

        summaries.append(
            f"{i}. {sub['number']} {sub['title']}\n"
            f"SUMMARY:\n{summary}\n"
        )

    return ("\n" + "-" * 80 + "\n").join(summaries)


def main():
    language = "pl"

    subtitles = extract_subtitles_from_pdf(pdf_path)
    summaries = get_summaries(subtitles, language)

    print(summaries)


if __name__ == "__main__":
    main()