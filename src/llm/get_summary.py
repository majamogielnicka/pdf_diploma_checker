import sys
from pathlib import Path
import requests
from get_subtitles import extract_subtitles_from_pdf

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_DIR))

pdf_path = SRC_DIR / "theses" / "zusz.pdf"

MODEL_PL = "SpeakLeash/bielik-7b-instruct-v0.1-gguf:latest"
MODEL_EN = "qwen2.5:latest"

PROMPT_PL = """Streść poniższy fragment pracy dyplomowej w dokładnie jednym zdaniu.

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
- return exactly one sentence
- do not repeat the instruction
- do not output the words "Requirements" or "Fragment"
- no quotes
- no bullet points
- preserve the meaning
- do not add information not present in the fragment
- if the fragment is incomplete, summarize only what can be inferred from it

Text to summarize:
"""


def get_summary(fragment, model, prompt):
    full_prompt = prompt + fragment

    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.2,
                "num_predict": 120
            }
        },
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