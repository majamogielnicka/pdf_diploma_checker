import sys
from pathlib import Path

from llama_cpp import Llama

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

try:
    from analysis.modules.llm.get_subtitles import extract_subtitles_from_pdf
except Exception:
    from get_subtitles import extract_subtitles_from_pdf

PDF_PATH = PROJECT_ROOT / "data" / "doro.pdf"
MODEL_PATH = BASE_DIR / "models" / "gemma3" / "gemma-3-4b-it-Q4_K_M.gguf"

PROMPT_PL = (
    "Na podstawie wyłącznie podanego tekstu napisz jedno zdanie streszczenia po polsku. "
    "Nie dodawaj żadnych informacji spoza tekstu. "
    "Nie używaj ogólników. "
    "Nie łącz wielu niezależnych definicji w jedno sztuczne zdanie. "
    "Jeśli tekst jest urwany lub niejednoznaczny, streść tylko to, co pewne. "
    "Zwróć tylko i wyłącznie zdanie wynikowe bez swojego wstępu.\n"
)

PROMPT_EN = (
    "Summarize the given fragment in one sentence in English. "
    "Do not add any information not present in the text. "
    "If the fragment is incomplete or ambiguous, summarize only what is certain. "
    "Return only the final sentence.\n"
)

MAX_FRAGMENT_CHARS = 2200
MAX_NEW_TOKENS = 80
N_CTX = 4096
N_THREADS = None
N_GPU_LAYERS = 0

_LLM = None


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


def get_llm():
    global _LLM

    if _LLM is None:
        _LLM = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False,
        )

    return _LLM


def build_prompt(fragment, language):
    prompt = get_prompt(language)

    if language == "pl":
        return f"{prompt}\nTEKST:\n{fragment}\n\nWYNIK:\n"
    return f"{prompt}\nTEXT:\n{fragment}\n\nRESULT:\n"


def get_summary(fragment, language):
    fragment = prepare_fragment(fragment)
    if not fragment:
        return "[PUSTY FRAGMENT]"

    llm = get_llm()
    full_prompt = build_prompt(fragment, language)

    output = llm(
        full_prompt,
        max_tokens=MAX_NEW_TOKENS,
        temperature=0.0,
        top_p=0.2,
        repeat_penalty=1.1,
        stop=["\n\n", "TEKST:", "TEXT:", "WYNIK:", "RESULT:"],
        echo=False,
    )

    text = output["choices"][0]["text"].strip()
    return text or "[BRAK ODPOWIEDZI MODELU]"


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

    if not MODEL_PATH.exists():
        print(f"Błąd: model nie istnieje: {MODEL_PATH}")
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