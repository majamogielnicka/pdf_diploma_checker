import sys
from pathlib import Path
2
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))
sys.path.append(str(current_dir.parents[4]))

import json
import config 
from document_parser import DocumentParser
from llava_engine import LlavaEngine
from reference_matcher import ReferenceMatcher
from consistency_checker import ConsistencyChecker

def main(pdf_path):
    parser = DocumentParser(pdf_path)
    llava = LlavaEngine()
    matcher = ReferenceMatcher()
    checker = ConsistencyChecker()

    paragraphs, images = parser.parse()
    final_report = []

    for img in images:
        img_id = img["id"]
        image_bytes = img["bytes"]

        refs = matcher.find_references(paragraphs, img_id)

        if not refs:
            final_report.append({
                "obrazek": img_id,
                "odwolanie": "brak",
                "poprawnosc_danych": "False",
                "bledy": ["Brak odwołania w tekście całej pracy."]
            })
            continue

        image_data = llava.extract_data(image_bytes)

        for ref_para in refs:
            verification = checker.check(ref_para, image_data)
            
            final_report.append({
                "obrazek": img_id,
                "odwolanie": "wystapilo",
                "poprawnosc_danych": verification.get("poprawnosc_danych", "False"),
                "bledy": verification.get("bledy", "None")
            })

    print(json.dumps(final_report, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) > 1: 
        main(sys.argv[1])
    else:
        print(f"Brak argumentu. Analizuję domyślny plik z config.py: {config.THESIS_PATH}")
        main(str(config.THESIS_PATH))