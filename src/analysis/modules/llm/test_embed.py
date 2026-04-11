import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

LANGUAGE = "pl"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"


def model_tag(model_name):
    tag = model_name.strip().split("/")[-1]
    tag = tag.replace(":", "_")
    tag = tag.replace("/", "_")
    tag = tag.replace("-", "_")
    tag = tag.replace(".", "_")
    return tag


OUTPUT_DIR = BASE_DIR / "analysis" / "modules" /"llm" / "wyniki" / model_tag(EMBEDDING_MODEL)

try:
    from analysis.modules.llm.get_purpose import get_purpose
except Exception:
    from get_purpose import get_purpose

try:
    from analysis.modules.llm.get_summary import summarize_subtitles
except Exception:
    from get_summary import summarize_subtitles

try:
    from analysis.modules.llm.similarity import compute_similarity_for_summaries
except Exception:
    from similarity import compute_similarity_for_summaries


def save_similarity_txt(pdf_path, result):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{Path(pdf_path).stem}_similarity.txt"

    lines = []
    lines.append(f"Plik: {Path(pdf_path).resolve()}")
    lines.append(f"Wygenerowano: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("MODEL EMBEDDINGÓW")
    lines.append(result.get("embedding_model") or "Brak")
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
    if not DATA_DIR.exists():
        print(f"Błąd: folder nie istnieje: {DATA_DIR}")
        return

    pdf_files = sorted(DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"Brak plików PDF w folderze: {DATA_DIR}")
        return

    print(f"Model embeddingów: {EMBEDDING_MODEL}")
    print(f"Folder wyników: {OUTPUT_DIR}")
    print(f"Liczba plików: {len(pdf_files)}")
    print("")

    for pdf_path in pdf_files:
        print(f"Analiza: {pdf_path.name}")
        purpose = get_purpose(pdf_path, LANGUAGE)
        summaries = summarize_subtitles(pdf_path, language=LANGUAGE)
        result = compute_similarity_for_summaries(purpose, summaries, EMBEDDING_MODEL)
        result["embedding_model"] = EMBEDDING_MODEL
        output_path = save_similarity_txt(pdf_path, result)
        print(f"Zapisano: {output_path}")
        print("")


if __name__ == "__main__":
    main()