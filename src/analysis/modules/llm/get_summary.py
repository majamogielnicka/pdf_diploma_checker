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

from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
from analysis.modules.llm.get_subtitles import extract_subtitles_from_pdf

PDF_PATH = PROJECT_ROOT / "data" / "inż_2_.pdf"

MODEL_PATH = Path.home() / "models" / "gemma2" / "gemma-2-9b-it-Q4_K_M.gguf"

MAX_FRAGMENT_CHARS = 1600
MAX_NEW_TOKENS = 96
N_CTX = 4096
N_THREADS = None
N_GPU_LAYERS = 0

PROMPT_PL = (
    "Na podstawie wyłącznie podanego fragmentu napisz jedno zdanie po polsku streszczające jego główną treść. "
    "Zdanie ma odnosić się tylko do informacji zawartych w tym fragmencie, bez odwołań do innych części pracy. "
    "Użyj stylu rzeczowego i możliwie bezosobowego. "
    "Nie dodawaj informacji spoza tekstu."
)

PROMPT_EN = (
    "Write one sentence in English expressing the main content of the fragment. "
    "Use an impersonal, content-focused style. "
    "Do not use phrases such as 'the section describes', 'the text presents', "
    "'the author discusses', or 'the paper explains'. "
    "Do not summarize the structure of the text; summarize its substantive content. "
    "Include the most important mechanism, property, goal, or result if present. "
    "Do not add any information not present in the text."
)

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
        top_p=0.1,
        repeat_penalty=1.12,
        stop=["\n\n", "TEKST:", "TEXT:", "WYNIK:", "RESULT:"],
        echo=False,
    )

    text = output["choices"][0]["text"].strip()

    return text or "[BRAK ODPOWIEDZI MODELU]"


def get_summaries(subtitles, language, verbose=False):
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
                "summary": "[BRAK TREŚCI W SEKCJI]",
            })

            if verbose:
                print(f"{i}/{len(subtitles)} - {display} -> BRAK TREŚCI")
                print("SUMMARY:")
                print("[BRAK TREŚCI W SEKCJI]")
                print("-" * 80)

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
            "summary": summary,
        })

        if verbose:
            print(f"{i}/{len(subtitles)} - {display}")
            print("SUMMARY:")
            print(summary)
            print("-" * 80)

    return summaries


def summarize_subtitles(raw_doc, subtitles=None, language="pl"):
    if subtitles is None:
        subtitles = extract_subtitles_from_pdf(raw_doc)

    return get_summaries(subtitles, language, verbose=False)


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

    raw_doc = extractPDF_llm(str(selected_pdf_path.resolve()))

    if raw_doc is None:
        print("Błąd: ekstrakcja PDF zwróciła None.")
        return

    subtitles = extract_subtitles_from_pdf(raw_doc)

    if not subtitles:
        print("Nie udało się wyciągnąć nagłówków / fragmentów z PDF.")
        return

    print(f"Wykryto nagłówków: {len(subtitles)}")

    summaries = get_summaries(subtitles, language, verbose=True)
    print_summaries(summaries)


if __name__ == "__main__":
    main()