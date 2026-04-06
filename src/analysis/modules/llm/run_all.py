from pathlib import Path
from get_purpose import get_purpose
from get_subtitles import extract_subtitles_from_pdf
from get_summary import get_summaries
from find_sota import find_sota_chapter

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

file_path = SRC_DIR / "theses" / "ch.pdf"
lng = "pl"

output_dir = SRC_DIR / "llm" / "wyniki"
results_path = output_dir / f"results_{file_path.stem}.txt"


def analyze_thesis(path, language):
    path = Path(path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    with open(results_path, "w", encoding="utf-8") as f:
        purpose = get_purpose(path, language)
        print("CEL", purpose)
        f.write(f"CEL:\n{purpose}\n\n")

        subtitles = extract_subtitles_from_pdf(path)
        summaries = get_summaries(subtitles, language)

        print(summaries)
        f.write("STRESZCZENIA ROZDZIAŁÓW I PODROZDZIAŁÓW:\n")
        f.write(f"{summaries}\n")

    print("\nRozpoczynam analizę SOTA...")
    find_sota_chapter(str(path), language=language, output_dir=str(output_dir))


def main():
    analyze_thesis(file_path, lng)


if __name__ == "__main__":
    main()