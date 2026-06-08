"""Generate one-sentence summaries for extracted thesis subtitle fragments."""

import sys
import os

from llama_cpp import Llama

_src_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for _p in (os.path.dirname(_src_dir), _src_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common.path import resource_path

from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
from analysis.modules.llm.get_subtitles import get_subtitles

from analysis.modules.llm.config import THESIS_PATH, MODEL_PATH, LANGUAGE, N_GPU_LAYERS

MAX_FRAGMENT_CHARS = 1600
MAX_NEW_TOKENS = 64
N_CTX = 2048
N_THREADS = max((os.cpu_count() or 4) - 1, 1)
N_BATCH = 512

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
    """Normalize whitespace and replace non-breaking spaces in input text."""

    if not text:
        return ""

    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def prepare_fragment(fragment):
    """Trim and shorten a fragment to fit model prompt constraints."""

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
    """Return language-specific summarization prompt template."""

    if language == "pl":
        return PROMPT_PL

    if language == "en":
        return PROMPT_EN

    raise ValueError("Nieobsługiwany język")


def get_llm():
    """Return the LLM instance, creating it once on first use."""

    global _LLM

    if _LLM is None:
        _LLM = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_batch=N_BATCH,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False,
        )

    return _LLM


def build_prompt(fragment, language):
    """Build the final prompt with language-specific input/output markers."""

    prompt = get_prompt(language)

    if language == "pl":
        return f"{prompt}\nTEKST:\n{fragment}\n\nWYNIK:\n"

    return f"{prompt}\nTEXT:\n{fragment}\n\nRESULT:\n"


def get_summary(fragment, language):
    """Generate a one-sentence summary for a single text fragment."""

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


def get_summaries(subtitles, language):
    """Generate summaries for all subtitle sections and return structured items."""

    summaries = []

    for i, sub in enumerate(subtitles, start=1):
        content = normalize_text(sub.get("content") or "")
        display = sub.get("display")
        number = sub.get("number")
        title = sub.get("title")

        if not display:
            display = f"{number or ''} {title or ''}".strip() or f"Sekcja {i}"

        if not content:
            item = {
                "index": i,
                "number": number,
                "title": title,
                "display": display,
                "content": content,
                "summary": "[BRAK TREŚCI W SEKCJI]",
            }
            summaries.append(item)
            print(item["display"])
            print("SUMMARY:")
            print(item["summary"])
            print()
            print("-" * 80)
            continue

        try:
            summary = get_summary(content, language)
        except Exception as e:
            summary = f"[BŁĄD GENEROWANIA: {e}]"

        item = {
            "index": i,
            "number": number,
            "title": title,
            "display": display,
            "content": content,
            "summary": summary,
        }
        summaries.append(item)
        print(item["display"])
        print("SUMMARY:")
        print(item["summary"])
        print()
        print("-" * 80)

    return summaries


def summarize_subtitles(raw_doc, subtitles, language):
    """Summarize subtitles, extracting them first when not provided."""

    if subtitles is None:
        subtitles = get_subtitles(raw_doc)

    return get_summaries(subtitles, language)


generate_summaries = summarize_subtitles


def print_summaries(summaries):
    """Print summaries in a readable console format."""

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
    """Run subtitle extraction and summary generation workflow."""

    pdf_path = THESIS_PATH
    language = LANGUAGE

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

    subtitles = get_subtitles(raw_doc)

    if not subtitles:
        print("Nie udało się wyciągnąć nagłówków / fragmentów z PDF.")
        return

    print("Podgląd subtitles po ekstrakcji (format jak w get_subtitles):")
    for sub in subtitles:
        display = normalize_text(sub.get("display") or "")
        content = normalize_text(sub.get("content") or "")
        if not display:
            display = normalize_text(sub.get("title") or "")
        preview = content[:250]
        if len(content) > 250:
            preview += "..."
        print(display)
        print(preview)
        print("-" * 80)

    print(f"Wykryto nagłówków: {len(subtitles)}")

    get_summaries(subtitles, language)


if __name__ == "__main__":
    main()