import sys
import json
import time
import traceback
from pathlib import Path
from datetime import datetime

"""
Skrypt analizuje wszystkie pliki PDF z folderu data.
Dla każdej pracy oblicza similarity oraz ocenę realizacji celu.
Wyniki zapisuje do plików result_nazwa.txt w folderze wyniki/test_DATA.
"""

BASE_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = BASE_DIR.parents[4]
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data" / "llm_mock"

TODAY = datetime.now().strftime("%Y-%m-%d")
RESULTS_DIR = PROJECT_ROOT / "wyniki" / f"test_{TODAY}"


for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)


from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text

from analysis.modules.llm.get_purpose import get_purpose
from analysis.modules.llm.config import EMBEDDING_MODEL, LANGUAGE, MODEL_PATH

from analysis.modules.llm.similarity import (
    compute_similarity_for_summaries,
)

from analysis.modules.llm.get_subtitles import (
    extract_subtitles_from_pdf,
)

from analysis.modules.llm.get_summary import (
    summarize_subtitles,
)

from analysis.modules.llm.goal_realization import (
    check_goal_realization,
)


def save_result_txt(
    output_path,
    pdf_path,
    purpose,
    similarity_result,
    purpose_realization_result,
    elapsed_time,
):
    lines = []

    lines.append("=" * 100)
    lines.append("WYNIK ANALIZY PRACY DYPLOMOWEJ")
    lines.append("=" * 100)
    lines.append("")
    lines.append(f"Plik PDF: {pdf_path.name}")
    lines.append(f"Ścieżka PDF: {pdf_path.resolve()}")
    lines.append(f"Wygenerowano: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"Czas przetwarzania: {elapsed_time:.2f} s")
    lines.append("")

    lines.append("=" * 100)
    lines.append("CEL PRACY")
    lines.append("=" * 100)
    lines.append(purpose or "Brak celu pracy")
    lines.append("")

    lines.append("=" * 100)
    lines.append("WYNIK SIMILARITY")
    lines.append("=" * 100)
    lines.append("")
    lines.append("ŚREDNIA PODOBIEŃSTWA COSINUSOWEGO:")
    lines.append(f"{similarity_result.get('average_similarity', 0.0):.6f}")
    lines.append("")

    lines.append("SZCZEGÓŁY DLA SEKCJI / STRESZCZEŃ:")
    lines.append("")

    for item in similarity_result.get("items", []):
        lines.append("-" * 100)
        lines.append(item.get("display") or item.get("title") or "Sekcja")
        lines.append("")
        lines.append("SUMMARY:")
        lines.append(item.get("summary") or "Brak")
        lines.append("")
        lines.append(
            f"COSINE_SIMILARITY: {float(item.get('cosine_similarity', 0.0)):.6f}"
        )
        lines.append("")

    lines.append("=" * 100)
    lines.append("OCENA REALIZACJI CELU")
    lines.append("=" * 100)
    lines.append("")
    lines.append(json.dumps(purpose_realization_result, ensure_ascii=False, indent=2))
    lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def save_error_txt(output_path, pdf_path, error_message):
    lines = []

    lines.append("=" * 100)
    lines.append("BŁĄD PODCZAS ANALIZY PRACY")
    lines.append("=" * 100)
    lines.append("")
    lines.append(f"Plik PDF: {pdf_path.name}")
    lines.append(f"Ścieżka PDF: {pdf_path.resolve()}")
    lines.append(f"Wygenerowano: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("TREŚĆ BŁĘDU:")
    lines.append(error_message)

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def process_single_pdf(pdf_path):
    start = time.perf_counter()

    print("=" * 100)
    print(f"Przetwarzanie: {pdf_path.name}")

    output_path = RESULTS_DIR / f"result_{pdf_path.stem}.txt"

    try:
        raw_doc = extractPDF_llm(str(pdf_path.resolve()))

        if raw_doc is None:
            raise ValueError("extractPDF_llm zwróciło None.")

        plain_text = get_plain_text(pdf_path)

        if not plain_text:
            raise ValueError("get_plain_text zwróciło pusty tekst.")

        purpose = get_purpose(plain_text, LANGUAGE)

        subtitles = extract_subtitles_from_pdf(raw_doc)

        summaries = summarize_subtitles(
            raw_doc,
            subtitles,
            LANGUAGE,
        )

        similarity_result = compute_similarity_for_summaries(
            purpose=purpose,
            summaries=summaries,
            embedding_model=EMBEDDING_MODEL,
        )

        purpose_realization_result = check_goal_realization(
            text=plain_text,
            purpose=purpose,
            language=LANGUAGE,
        )

        elapsed_time = time.perf_counter() - start

        save_result_txt(
            output_path=output_path,
            pdf_path=pdf_path,
            purpose=purpose,
            similarity_result=similarity_result,
            purpose_realization_result=purpose_realization_result,
            elapsed_time=elapsed_time,
        )

        print(f"Zapisano wynik: {output_path}")
        print(f"Czas: {elapsed_time:.2f} s")

    except Exception:
        elapsed_time = time.perf_counter() - start
        error_message = traceback.format_exc()

        save_error_txt(
            output_path=output_path,
            pdf_path=pdf_path,
            error_message=error_message,
        )

        print(f"Błąd dla pliku: {pdf_path.name}")
        print(f"Zapisano błąd do: {output_path}")
        print(f"Czas do błędu: {elapsed_time:.2f} s")


def main():
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"RESULTS_DIR: {RESULTS_DIR}")
    print("")

    if not DATA_DIR.exists():
        print(f"Błąd: folder data nie istnieje: {DATA_DIR}")
        return

    if not MODEL_PATH.exists():
        print(f"Błąd: model LLM nie istnieje: {MODEL_PATH}")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"Brak plików PDF w folderze: {DATA_DIR}")
        return

    print(f"Znaleziono {len(pdf_files)} plików PDF.")
    print("")

    global_start = time.perf_counter()

    for pdf_path in pdf_files:
        process_single_pdf(pdf_path)

    global_elapsed = time.perf_counter() - global_start

    print("=" * 100)
    print("Zakończono analizę wszystkich prac.")
    print(f"Folder wyników: {RESULTS_DIR}")
    print(f"Łączny czas działania: {global_elapsed:.2f} s")


if __name__ == "__main__":
    main()