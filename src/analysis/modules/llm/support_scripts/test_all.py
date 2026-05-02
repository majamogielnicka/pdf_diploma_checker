import sys
import time
import traceback
import importlib
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"

for p in (PROJECT_ROOT, SRC_DIR, BASE_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)


def import_function(module_names, function_names):
    errors = []

    for module_name in module_names:
        try:
            importlib.invalidate_caches()
            module = importlib.import_module(module_name)
            module = importlib.reload(module)
        except Exception as e:
            errors.append(f"[IMPORT] {module_name}: {e}")
            continue

        for function_name in function_names:
            func = getattr(module, function_name, None)
            if callable(func):
                return func, None

        errors.append(
            f"[BRAK FUNKCJI] {module_name}: nie znaleziono żadnej z funkcji {function_names}"
        )

    return None, "\n".join(errors)


def save_result_txt(result, pdf_path, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{pdf_path.stem}_results.txt"

    lines = []
    lines.append(f"Plik: {result['input_file']}")
    lines.append(f"Wygenerowano: {result['generated_at']}")
    lines.append("")
    lines.append("ŚREDNIA PODOBIEŃSTWA COSINUSOWEGO")
    if result.get("average_similarity") is not None:
        lines.append(f"{result['average_similarity']:.6f}")
    else:
        lines.append("Brak")
    lines.append("")
    lines.append("NAZWA PRACY")
    lines.append(result.get("thesis_name") or pdf_path.stem)
    lines.append("")
    lines.append("CEL PRACY")
    lines.append(result["purpose"] if result["purpose"] else "Brak")
    lines.append("")
    lines.append("PODOBIEŃSTWO DLA STRESZCZEŃ")
    lines.append("")

    summaries = result.get("heading_summaries")

    if summaries:
        for item in summaries:
            display = item.get("display")
            number = item.get("number")
            title = item.get("title")
            summary = item.get("summary") or ""
            cosine_similarity = item.get("cosine_similarity")

            if display:
                lines.append(display)
            elif number and title:
                lines.append(f"{number} {title}")
            elif title:
                lines.append(title)
            else:
                lines.append("Sekcja")

            lines.append("SUMMARY:")
            lines.append(summary.strip() if summary else "Brak streszczenia")

            if cosine_similarity is not None:
                lines.append(f"COSINE_SIMILARITY: {cosine_similarity:.6f}")
            else:
                lines.append("COSINE_SIMILARITY: Brak")

            lines.append("")
            lines.append("-" * 80)
            lines.append("")
    else:
        lines.append("Brak")
        lines.append("")

    lines.append("BŁĘDY")
    if result["errors"]:
        for key, value in result["errors"].items():
            lines.append(f"{key}: {value}")
    else:
        lines.append("Brak")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path


def save_summary_txt(summary_rows, output_dir, total_seconds, ok_count, fail_count):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "summary.txt"

    lines = []
    lines.append("TEST ALL - PODSUMOWANIE")
    lines.append(f"Wygenerowano: {datetime.now().isoformat()}")
    lines.append(f"Katalog danych: {DATA_DIR}")
    lines.append(f"Liczba plików OK: {ok_count}")
    lines.append(f"Liczba plików z błędem: {fail_count}")
    lines.append(f"Łączny czas [s]: {total_seconds:.2f}")
    lines.append("")

    for row in summary_rows:
        lines.append(f"PLIK: {row['file_name']}")
        lines.append(f"CZAS [s]: {row['duration_seconds']:.2f}")
        lines.append(f"STATUS: {row['status']}")
        lines.append(f"WYNIK: {row['output_path']}")
        if row.get("error"):
            lines.append(f"BŁĄD: {row['error']}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path


def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = BASE_DIR / f"test_all_{date_str}"
    output_dir.mkdir(parents=True, exist_ok=True)

    analyze_thesis, import_error = import_function(
        module_names=[
            "analysis.modules.llm.run_all",
            "run_all",
        ],
        function_names=[
            "analyze_thesis",
        ],
    )

    if analyze_thesis is None:
        print("Błąd importu analyze_thesis:")
        print(import_error)
        return

    pdf_files = sorted(DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"Brak plików PDF w katalogu: {DATA_DIR}")
        return

    print(f"Znaleziono {len(pdf_files)} plik(ów) PDF.")
    print(f"Wyniki będą zapisywane do: {output_dir}")
    print("Start...\n")

    total_start = time.perf_counter()
    summary_rows = []
    ok_count = 0
    fail_count = 0

    for i, pdf_path in enumerate(pdf_files, start=1):
        print(f"[{i}/{len(pdf_files)}] Przetwarzanie: {pdf_path.name}")
        file_start = time.perf_counter()

        try:
            result = analyze_thesis(pdf_path)
            output_path = save_result_txt(result, pdf_path, output_dir)
            duration = time.perf_counter() - file_start

            summary_rows.append(
                {
                    "file_name": pdf_path.name,
                    "duration_seconds": duration,
                    "status": "OK",
                    "output_path": str(output_path),
                    "error": None,
                }
            )

            ok_count += 1
            print(f"  OK | czas: {duration:.2f} s | zapis: {output_path}")

        except Exception as e:
            duration = time.perf_counter() - file_start
            error_text = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

            error_file = output_dir / f"{pdf_path.stem}_error.txt"
            error_file.write_text(error_text, encoding="utf-8")

            summary_rows.append(
                {
                    "file_name": pdf_path.name,
                    "duration_seconds": duration,
                    "status": "ERROR",
                    "output_path": str(error_file),
                    "error": f"{type(e).__name__}: {e}",
                }
            )

            fail_count += 1
            print(f"  ERROR | czas: {duration:.2f} s | szczegóły: {error_file}")

        print()

    total_seconds = time.perf_counter() - total_start
    summary_path = save_summary_txt(
        summary_rows=summary_rows,
        output_dir=output_dir,
        total_seconds=total_seconds,
        ok_count=ok_count,
        fail_count=fail_count,
    )

    print("KONIEC")
    print(f"Łączny czas: {total_seconds:.2f} s")
    print(f"OK: {ok_count} | ERROR: {fail_count}")
    print(f"Podsumowanie: {summary_path}")


if __name__ == "__main__":
    main()