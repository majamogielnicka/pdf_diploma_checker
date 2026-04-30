import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text

from analysis.modules.llm.get_purpose import get_purpose
from analysis.modules.llm.get_subtitles import get_subtitles
from analysis.modules.llm.get_summary import get_summaries
from analysis.modules.llm.similarity import compute_similarity_for_summaries, EMBEDDING_MODEL


DEFAULT_PDF_PATH = PROJECT_ROOT / "data" / "bosh.pdf"
DEFAULT_LANGUAGE = "pl"
threshold = 0.5


def calculate_embedding_grade(purpose, summaries):
    similarity_result = compute_similarity_for_summaries(
        purpose=purpose,
        summaries=summaries,
        embedding_model=EMBEDDING_MODEL,
    )

    items = similarity_result.get("items", [])
    total_sections = len(items)

    if total_sections == 0:
        return {
            "grade": 0.0,
            "max_grade": 60.0,
            "s_emb": 0.0,
            "threshold": threshold,
            "total_sections": 0,
            "off_topic_sections": 0,
            "p_off": 100.0,
            "items": [],
        }

    off_topic_sections = 0

    for item in items:
        cosine_similarity = float(item.get("cosine_similarity", 0.0))
        below_threshold = cosine_similarity < threshold
        item["below_threshold"] = below_threshold

        if below_threshold:
            off_topic_sections += 1

    p_off = (off_topic_sections / total_sections) * 100.0
    s_emb = 100.0 - p_off
    grade = 0.60 * s_emb

    return {
        "grade": round(grade, 2),
        "max_grade": 60.0,
        "s_emb": round(s_emb, 2),
        "threshold": threshold,
        "total_sections": total_sections,
        "off_topic_sections": off_topic_sections,
        "p_off": round(p_off, 2),
        "items": items,
    }


def get_content_grade(purpose, summaries):
    return calculate_embedding_grade(
        purpose=purpose,
        summaries=summaries
    )


def main():
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF_PATH
    language = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_LANGUAGE

    print(f"PDF_PATH: {pdf_path}")
    print(f"PDF_EXISTS: {pdf_path.exists()}")
    print(f"PDF_ABSOLUTE: {pdf_path.resolve()}")

    if not pdf_path.exists():
        print(f"Błąd: plik nie istnieje: {pdf_path}")
        return

    raw_doc = extractPDF_llm(str(pdf_path.resolve()))

    if raw_doc is None:
        print("Błąd: extractPDF_llm zwróciło None.")
        return

    plain_text = get_plain_text(pdf_path)

    purpose = get_purpose(plain_text, language=language)

    subtitles = get_subtitles(raw_doc)
    summaries = get_summaries(subtitles, language=language)

    result = get_content_grade(
        purpose=purpose,
        summaries=summaries
    )

    print("CEL PRACY:")
    print(purpose)
    print()
    print("OCENA EMBEDDINGOWA:")
    print(f"{result['grade']} / {result['max_grade']}")
    print()
    print(f"S_emb: {result['s_emb']}")
    print(f"Próg: {result['threshold']}")
    print(f"Liczba podrozdziałów: {result['total_sections']}")
    print(f"Poniżej progu: {result['off_topic_sections']}")
    print(f"P_off: {result['p_off']}%")


if __name__ == "__main__":
    main()