from pathlib import Path
from get_purpose import get_purpose
from get_content import split_subtitles
from get_summary import get_summaries
from find_sota import find_sota_chapter

file_path, lng = Path("src/theses/jago.pdf"), "pl"

output_dir = Path("src/llm/wyniki")
results_path = output_dir / "results.txt"

def analyze_thesis(path, language):
    if not path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, "w", encoding="utf-8") as f:
        purpose = get_purpose(path, language)
        print("CEL ", purpose)
        f.write(f"cel: {purpose}\n")

        subtitles = split_subtitles(path)
        summaries = get_summaries(subtitles, language)
        
        find_sota_chapter(str(path), output_dir=str(output_dir))

        print(summaries)
        f.write(f"{summaries}\n")

def main():
    analyze_thesis(file_path, lng)

if __name__ == "__main__":
    main()