import sys
from datetime import datetime
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = BASE_DIR / "wyniki"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

try:
    from analysis.modules.llm.get_subtitles import extract_subtitles_from_pdf
except Exception:
    from get_subtitles import extract_subtitles_from_pdf


DEFAULT_PDF_PATH = PROJECT_ROOT / "data" / "zusz.pdf"

# MODEL_PL = "SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M"
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


def get_thesis_name(pdf_path: Path) -> str:
    return pdf_path.stem


def get_summary(fragment: str, model: str, prompt: str) -> str:
    fragment = (fragment or "").strip()
    if not fragment:
        return ""

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
                "num_predict": 200,
                "num_ctx": 2048,
            },
        },
        timeout=120,
    )

    if not resp.ok:
        raise RuntimeError(f"Ollama {resp.status_code}: {resp.text}")

    data = resp.json()
    return data.get("response", "").strip()


def summarize_subtitles(pdf_path, subtitles=None, language="pl"):
    pdf_path = Path(pdf_path)

    if subtitles is None:
        subtitles = extract_subtitles_from_pdf(pdf_path)

    if language == "pl":
        model = MODEL_PL
        prompt = PROMPT_PL
    elif language == "en":
        model = MODEL_EN
        prompt = PROMPT_EN
    else:
        raise ValueError("Nieobsługiwany język")

    results = []

    for sub in subtitles:
        content = (sub.get("content") or "").strip()
        if not content:
            continue

        summary = get_summary(content, model, prompt)

        number = sub.get("number")
        title = sub.get("title")
        display = sub.get("display")

        if not display:
            if number and title:
                display = f"{number} {title}"
            elif title:
                display = title
            elif number:
                display = str(number)
            else:
                display = "Sekcja"

        results.append(
            {
                "number": number,
                "title": title,
                "display": display,
                "summary": summary,
            }
        )

    return results


generate_summaries = summarize_subtitles


def save_summaries_txt(pdf_path: Path, summaries, thesis_name: str | None = None) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pdf_path = Path(pdf_path)
    thesis_name = thesis_name or get_thesis_name(pdf_path)
    output_path = OUTPUT_DIR / f"{pdf_path.stem}_summaries.txt"

    lines = []
    lines.append(f"Plik: {pdf_path.resolve()}")
    lines.append(f"Wygenerowano: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("NAZWA PRACY")
    lines.append(thesis_name)
    lines.append("")
    lines.append("STRESZCZENIA NAGŁÓWKÓW")

    if summaries:
        for item in summaries:
            lines.append(item.get("display") or "Sekcja")
            lines.append(item.get("summary") or "Brak streszczenia")
            lines.append("")
    else:
        lines.append("Brak")
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path


def main():
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF_PATH
    language = sys.argv[2] if len(sys.argv) > 2 else "pl"

    if not pdf_path.exists():
        print(f"Błąd: plik nie istnieje: {pdf_path}")
        return

    thesis_name = get_thesis_name(pdf_path)
    subtitles = extract_subtitles_from_pdf(pdf_path)
    summaries = summarize_subtitles(pdf_path, subtitles, language)
    output_path = save_summaries_txt(pdf_path, summaries, thesis_name)

    print(f"Nazwa pracy: {thesis_name}")
    print(f"Wynik zapisano do: {output_path}")


if __name__ == "__main__":
    main()