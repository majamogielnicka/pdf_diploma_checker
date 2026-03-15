from pathlib import Path
from get_purpose import get_purpose
from get_content import split_subtitles
from get_summary import get_summaries

file_path, lng = Path("src/theses/doro.pdf"), "pl" #pl or en
results_path = Path(__file__).resolve().parent / "results.txt"

def analyze_thesis(path, language):
    
    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku")
    
    with open(results_path, "w", encoding="utf-8") as f:
        purpose = get_purpose(path, language)
        print("CEL ", purpose)
        f.write(f"cel: {purpose}\n")

        subtitles = split_subtitles(path)
        summaries = get_summaries(subtitles, language)

        print(summaries)
        f.write(f"{summaries}\n")


def main():
    analyze_thesis(file_path, lng)


if __name__ == "__main__":
    main()