import sys
from pathlib import Path
from datetime import datetime

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_DIR = BASE_DIR / "wyniki"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

try:
    from analysis.modules.llm.get_purpose import get_purpose
except Exception:
    from get_purpose import get_purpose

try:
    from analysis.modules.llm.get_summary import summarize_subtitles
except Exception:
    from get_summary import summarize_subtitles


DEFAULT_PDF_PATH = PROJECT_ROOT / "data" / "zusz.pdf"

EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"


def normalize_text(text):
    if not text:
        return ""
    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def get_purpose_text_for_embedding(text):
    text = normalize_text(text)
    return f"search_query: {text}"


def get_summary_text_for_embedding(text):
    text = normalize_text(text)
    return f"search_document: {text}"


def compute_similarity_for_summaries(purpose, summaries):
    purpose = normalize_text(purpose)
    items = []

    for item in summaries or []:
        new_item = dict(item)
        new_item["summary"] = normalize_text(new_item.get("summary") or "")
        items.append(new_item)

    if not purpose:
        for item in items:
            item["cosine_similarity"] = 0.0
        return {
            "purpose": purpose,
            "items": items,
            "average_similarity": 0.0,
        }

    texts = []
    valid_indices = []

    for i, item in enumerate(items):
        summary = item["summary"]
        if summary:
            valid_indices.append(i)
            texts.append(get_summary_text_for_embedding(summary))

    if not texts:
        for item in items:
            item["cosine_similarity"] = 0.0
        return {
            "purpose": purpose,
            "items": items,
            "average_similarity": 0.0,
        }

    model = SentenceTransformer(
        EMBEDDING_MODEL,
        trust_remote_code=True
    )

    purpose_embedding = model.encode(
        [get_purpose_text_for_embedding(purpose)],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    text_embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores = cosine_similarity(purpose_embedding, text_embeddings).flatten()

    for item in items:
        item["cosine_similarity"] = 0.0

    for idx, score in zip(valid_indices, scores):
        items[idx]["cosine_similarity"] = float(score)

    average_similarity = float(scores.mean()) if len(scores) > 0 else 0.0

    return {
        "purpose": purpose,
        "items": items,
        "average_similarity": average_similarity,
    }


def save_similarity_txt(pdf_path, result):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{Path(pdf_path).stem}_similarity.txt"

    lines = []
    lines.append(f"Plik: {Path(pdf_path).resolve()}")
    lines.append(f"Wygenerowano: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("ŚREDNIA PODOBIEŃSTWA COSINUSOWEGO")
    lines.append(f"{result.get('average_similarity', 0.0):.6f}")
    lines.append("")
    lines.append("CEL PRACY")
    lines.append(result.get("purpose") or "Brak")
    lines.append("")
    lines.append("PODOBIEŃSTWO DLA STRESZCZEŃ")
    lines.append("")

    for item in result.get("items", []):
        lines.append(item.get("display") or "Sekcja")
        lines.append("SUMMARY:")
        lines.append(item.get("summary") or "Brak")
        lines.append(f"COSINE_SIMILARITY: {item.get('cosine_similarity', 0.0):.6f}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path


def main():
    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF_PATH
    language = sys.argv[2] if len(sys.argv) > 2 else "pl"

    if not pdf_path.exists():
        print(f"Błąd: plik nie istnieje: {pdf_path}")
        return

    purpose = get_purpose(pdf_path, language)
    summaries = summarize_subtitles(pdf_path, language=language)
    result = compute_similarity_for_summaries(purpose, summaries)
    output_path = save_similarity_txt(pdf_path, result)

    print(f"Wynik zapisano do: {output_path}")


if __name__ == "__main__":
    main()