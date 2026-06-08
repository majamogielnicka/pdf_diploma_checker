import os
import sys
import json
import time
import argparse
import traceback
from pathlib import Path


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SCRIPT_DIR = Path(__file__).resolve().parent

EXTRACTION_DIR = os.path.join(BASE_DIR, "analysis", "extraction")
COMMON_DIR = os.path.join(BASE_DIR, "common")
LINGUISTICS_DIR = os.path.join(BASE_DIR, "analysis", "modules", "linguistics")
LLM_DIR = os.path.join(BASE_DIR, "analysis", "modules", "llm")
REDACTION_DIR = os.path.join(BASE_DIR, "analysis", "modules", "redaction")

for path in [BASE_DIR, EXTRACTION_DIR, COMMON_DIR, LINGUISTICS_DIR, LLM_DIR, REDACTION_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)


DEFAULT_THESIS_PATH = SCRIPT_DIR / "jago.pdf"
DEFAULT_LANGUAGE = "pl"


def debug_print(title, value=None):
    print()
    print(f"=== {title} ===", flush=True)

    if value is not None:
        if isinstance(value, (dict, list, tuple)):
            try:
                print(json.dumps(value, ensure_ascii=False, indent=2), flush=True)
            except Exception:
                print(value, flush=True)
        else:
            print(value, flush=True)

    print("=" * (len(title) + 8), flush=True)


def _display_for_item(item, fallback_idx):
    return (
        item.get("display")
        or item.get("heading")
        or item.get("title")
        or item.get("subtitle")
        or f"Section {fallback_idx}"
    )


def run_embedding_grade_test(pdf_path, language):
    started = time.perf_counter()

    from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
    from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
    from analysis.modules.llm.get_purpose import get_purpose
    from analysis.modules.llm.get_subtitles import get_subtitles
    from analysis.modules.llm.get_summary import get_summaries
    from analysis.modules.llm.get_grade import calculate_embedding_grade, get_content_grade

    pdf_path = Path(pdf_path).expanduser().resolve()

    debug_print("START", {
        "pdf_path": str(pdf_path),
        "language": language,
    })

    if not pdf_path.exists():
        raise FileNotFoundError(f"Plik nie istnieje: {pdf_path}")

    debug_print("1. PLAIN TEXT", "get_plain_text(pdf_path)")
    plain_text = get_plain_text(str(pdf_path))

    debug_print("PLAIN TEXT INFO", {
        "length": len(plain_text or ""),
        "is_empty": not bool(plain_text),
    })

    if not plain_text:
        raise ValueError("Pusty plain text - nie można wyznaczyć celu pracy.")

    debug_print("2. CEL PRACY", "get_purpose(plain_text, language)")
    purpose = get_purpose(plain_text, language)

    debug_print("PURPOSE", purpose)

    if not purpose:
        raise ValueError("Pusty cel pracy - nie można policzyć embedding grade.")

    debug_print("3. STRUKTURA DOKUMENTU", "extractPDF_llm(pdf_path)")
    raw_doc = extractPDF_llm(str(pdf_path))

    if raw_doc is None:
        raise ValueError("extractPDF_llm zwrócił None")

    debug_print("4. SUBTITLES", "get_subtitles(raw_doc)")
    subtitles = get_subtitles(raw_doc)

    debug_print("SUBTITLES INFO", {
        "count": len(subtitles or []),
    })

    debug_print("5. SUMMARIES", "get_summaries(subtitles, language)")
    summaries = get_summaries(subtitles, language)

    debug_print("SUMMARIES INFO", {
        "count": len(summaries or []),
    })

    debug_print("6. EMBEDDING RESULT", "calculate_embedding_grade(purpose, summaries)")
    embedding_result = calculate_embedding_grade(
        purpose=purpose,
        summaries=summaries,
    )

    debug_print("EMBEDDING RESULT RAW", embedding_result)

    debug_print("7. CONTENT GRADE WRAPPER", "get_content_grade(purpose, summaries)")
    content_res = get_content_grade(purpose, summaries)

    if isinstance(content_res, tuple) and len(content_res) == 2:
        content_grade_value, off_topic_headings = content_res
    else:
        content_grade_value = content_res if isinstance(content_res, (int, float)) else 0.0
        off_topic_headings = []

    debug_print("CONTENT GRADE VALUE", content_grade_value)
    debug_print("OFF TOPIC HEADINGS", off_topic_headings)

    items = embedding_result.get("items", [])
    threshold = float(embedding_result.get("threshold", 0.0))
    total_sections = int(embedding_result.get("total_sections", len(items)))
    off_topic_sections = int(embedding_result.get("off_topic_sections", 0))

    debug_print("8. PER SECTION COSINE", {
        "threshold": threshold,
        "sections": [
            {
                "idx": idx,
                "section": _display_for_item(item, idx),
                "cosine_similarity": round(float(item.get("cosine_similarity", 0.0)), 6),
                "below_threshold": bool(item.get("below_threshold", False)),
            }
            for idx, item in enumerate(items, start=1)
        ],
    })

    p_off = (off_topic_sections / total_sections) * 100.0 if total_sections > 0 else 100.0
    s_emb = 100.0 - p_off
    recomputed_grade = round(s_emb, 2)

    debug_print("9. LICZENIE OCENY (TYLKO EMBEDDING)", {
        "wzor": "p_off = (off_topic_sections / total_sections) * 100; grade = 100 - p_off",
        "off_topic_sections": off_topic_sections,
        "total_sections": total_sections,
        "p_off": round(p_off, 2),
        "s_emb": round(s_emb, 2),
        "grade_recomputed": recomputed_grade,
        "grade_from_calculate_embedding_grade": embedding_result.get("grade", 0.0),
        "grade_from_get_content_grade": content_grade_value,
    })

    elapsed = time.perf_counter() - started

    result = {
        "purpose": purpose,
        "content_grade": float(content_grade_value),
        "off_topic_headings": off_topic_headings,
        "embedding_result": embedding_result,
        "elapsed_seconds": round(elapsed, 2),
    }

    debug_print("FINISH", {
        "elapsed_seconds": round(elapsed, 2),
        "note": "Bez goal_realization i bez SOTA - tylko content/embedding grade.",
    })

    return result


def parse_args():
    parser = argparse.ArgumentParser(
        description="Debug test: tylko content/embedding grade z logiką jak w pipeline."
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=str(DEFAULT_THESIS_PATH),
        help="Ścieżka do PDF.",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default=DEFAULT_LANGUAGE,
        choices=["pl", "en"],
        help="Język analizy.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print()
    print("=== TEST EMBEDDING GRADE (PIPELINE LOGIC) ===", flush=True)
    print(f"PDF: {args.pdf}", flush=True)
    print(f"LANG: {args.lang}", flush=True)
    print("=============================================", flush=True)

    result = run_embedding_grade_test(
        pdf_path=args.pdf,
        language=args.lang,
    )

    print()
    print("=== RESULT JSON ===", flush=True)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    print("===================", flush=True)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print()
        print("=== TRACEBACK ===", flush=True)
        traceback.print_exc()
        raise