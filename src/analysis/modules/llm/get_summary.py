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

from analysis.extraction.get_subtitles import extract_subtitles_from_pdf

PDF_PATH = PROJECT_ROOT / "data" / "inż_2_.pdf"

MODEL_NAME = "gemma3local"

PROMPT_PL = (
    "Na podstawie wyłącznie podanego tekstu napisz jedno zdanie streszczenia po polsku. "
    "Nie dodawaj żadnych informacji spoza tekstu. "
    "Nie używaj ogólników. "
    "Nie łącz wielu niezależnych definicji w jedno sztuczne zdanie. "
    "Jeśli tekst jest urwany lub niejednoznaczny, streść tylko to, co pewne."
    "Zwróć tylko i wylacznie zdanie wynikowe bez swojego wstepu\n"
)
PROMPT_EN = "Summarize the given fragment in one sentence in English:\n"

MAX_FRAGMENT_CHARS = 2200
REQUEST_TIMEOUT = 120


def normalize_text(text):
    if not text:
        return ""
    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def prepare_fragment(fragment):
    text = normalize_text(fragment)
    if not text:
        return ""

    if len(text) <= MAX_FRAGMENT_CHARS:
        return text

    cut = text[:MAX_FRAGMENT_CHARS]

    last_dot = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if last_dot > int(MAX_FRAGMENT_CHARS * 0.6):
        return cut[: last_dot + 1].strip()

    last_space = cut.rfind(" ")
    if last_space > 0:
        return cut[:last_space].strip()

    return cut.strip()


def get_prompt(language):
    if language == "pl":
        return PROMPT_PL
    if language == "en":
        return PROMPT_EN
    raise ValueError("Nieobsługiwany język")


def get_summary(fragment, language):
    fragment = prepare_fragment(fragment)
    if not fragment:
        return "[PUSTY FRAGMENT]"

    prompt = get_prompt(language)
    full_prompt = prompt + fragment

    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL_NAME,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.2,
                "num_predict": 80,
                "num_ctx": 1024,
                "repeat_penalty": 1.1
            }
        },
        timeout=REQUEST_TIMEOUT
    )

    if not resp.ok:
        raise RuntimeError(f"Ollama {resp.status_code}: {resp.text}")

    return resp.json()["response"].strip()


def get_summaries(subtitles, language):
    summaries = []

    for i, sub in enumerate(subtitles, start=1):
        content = normalize_text(sub.get("content") or "")
        display = sub.get("display")
        number = sub.get("number")
        title = sub.get("title")

        if not display:
            display = f"{number or ''} {title or ''}".strip() or f"Sekcja {i}"

        if not content:
            summaries.append({
                "index": i,
                "number": number,
                "title": title,
                "display": display,
                "content": content,
                "summary": "[BRAK TREŚCI W SEKCJI]"
            })
            print(f"{i}/{len(subtitles)} - {display} -> BRAK TREŚCI")
            continue

        try:
            summary = get_summary(content, language)
        except Exception as e:
            summary = f"[BŁĄD GENEROWANIA: {e}]"

        summaries.append({
            "index": i,
            "number": number,
            "title": title,
            "display": display,
            "content": content,
            "summary": summary
        })

        print(f"{i}/{len(subtitles)} - {display}")

    return summaries


def summarize_subtitles(pdf_path, subtitles=None, language="pl"):
    pdf_path = Path(pdf_path)

    if subtitles is None:
        subtitles = extract_subtitles_from_pdf(pdf_path)

    return get_summaries(subtitles, language)


generate_summaries = summarize_subtitles


def print_summaries(summaries):
    if not summaries:
        print("Brak")
        return

    for item in summaries:
        print(item["display"])
        print("SUMMARY:")
        print(item["summary"])
        print()
        print("-" * 80)


def main():
    selected_pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_PATH
    language = sys.argv[2] if len(sys.argv) > 2 else "pl"

    if not selected_pdf_path.exists():
        print(f"Błąd: plik nie istnieje: {selected_pdf_path}")
        return

    subtitles = extract_subtitles_from_pdf(selected_pdf_path)

    if not subtitles:
        print("Nie udało się wyciągnąć nagłówków / fragmentów z PDF.")
        return

    print(f"Wykryto nagłówków: {len(subtitles)}")

    summaries = get_summaries(subtitles, language)

    print()
    print_summaries(summaries)


if __name__ == "__main__":
    main()