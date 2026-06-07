import os
import sys
import json
import time
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


# Testujemy tę samą pracę, która leży obok pipeline.py / tego skryptu
THESIS_PATH = SCRIPT_DIR / "jost2.pdf"

# Język pracy
LANGUAGE = "en"


def main():
    print("=== TEST PURPOSE RESULT ===")
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"SCRIPT_DIR: {SCRIPT_DIR}")
    print(f"THESIS_PATH: {THESIS_PATH}")
    print(f"LANGUAGE: {LANGUAGE}")
    print()

    if not THESIS_PATH.exists():
        print(f"ERROR: thesis file does not exist: {THESIS_PATH}")
        return 1

    from analysis.modules.llm.config import MODEL_PATH
    from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
    from analysis.modules.llm.get_purpose import get_purpose
    from analysis.modules.llm.goal_realization import (
        check_goal_realization,
        get_score_from_goal_result,
        extract_ending_fragment,
    )

    print(f"MODEL_PATH: {MODEL_PATH}")
    print(f"MODEL_EXISTS: {Path(MODEL_PATH).exists()}")
    print()

    if not Path(MODEL_PATH).exists():
        print("ERROR: model does not exist, goal realization will return 0.")
        return 1

    start = time.perf_counter()

    print("1. Reading plain text...")
    plain_text = get_plain_text(str(THESIS_PATH))
    print(f"plain_text length: {len(plain_text or '')}")
    print()

    if not plain_text:
        print("ERROR: plain_text is empty.")
        return 1

    print("2. Extracting purpose...")
    purpose = get_purpose(plain_text, LANGUAGE)
    print()
    print("=== PURPOSE ===")
    print(purpose)
    print()

    if not purpose:
        print("ERROR: purpose is empty.")
        return 1

    print("3. Extracting ending fragment...")
    ending_fragment = extract_ending_fragment(plain_text)
    print(f"ending_fragment length: {len(ending_fragment or '')}")
    print()
    print("=== ENDING FRAGMENT PREVIEW ===")
    print((ending_fragment or "")[:2000])
    print()

    if not ending_fragment:
        print("ERROR: ending fragment is empty.")
        return 1

    print("4. Checking goal realization...")
    goal_result = check_goal_realization(
        text=plain_text,
        purpose=purpose,
        language=LANGUAGE,
    )

    purpose_score = get_score_from_goal_result(goal_result)

    print()
    print("=== GOAL RESULT JSON ===")
    print(json.dumps(goal_result, ensure_ascii=False, indent=2))

    print()
    print("=== PURPOSE SCORE ===")
    print(purpose_score)

    elapsed = time.perf_counter() - start
    print()
    print(f"Execution time: {elapsed:.2f} s")

    if purpose_score == 100:
        print("RESULT: OK, goal realization gives 100.")
    elif purpose_score == 0:
        print("RESULT: PROBLEM, goal realization gives 0.")
    else:
        print(f"RESULT: goal realization gives {purpose_score}.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print()
        print("=== TRACEBACK ===")
        traceback.print_exc()
        raise