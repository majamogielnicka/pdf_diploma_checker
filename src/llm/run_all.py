from pathlib import Path
from get_purpose import get_purpose
# from get_summary import get_summary
# from get_headings import get_headings

file_path, language = Path("src/theses/doro.pdf"), "pl" #pl or en
results_path = Path(__file__).resolve().parent / "results.txt"

def analyze_thesis(path):
    
    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku")
    
    with open(results_path, "w", encoding="utf-8") as f:
        purpose = get_purpose(path, language)
        print(purpose)
        f.write(f"{purpose}\n")

        # headings = get_headings(path)
        # for heading in headings:
        #     summary = get_summary(path, heading)
        #     f.write(f"{summary}\n")

def main():
    analyze_thesis(file_path)


if __name__ == "__main__":
    main()