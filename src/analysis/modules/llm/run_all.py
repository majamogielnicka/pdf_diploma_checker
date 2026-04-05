import sys
import traceback
import importlib
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

file_path = PROJECT_ROOT / "data" / "zusz.pdf"
OUTPUT_DIR = BASE_DIR / "wyniki"


def import_function(module_names, function_names):
    errors = []

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
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


def try_call(func, *variants):
    last_type_error = None

    for args, kwargs in variants:
        try:
            return func(*args, **kwargs), None
        except TypeError as e:
            last_type_error = e
        except Exception as e:
            return None, f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

    if last_type_error is not None:
        return None, f"TypeError: {last_type_error}"

    return None, "Nie udało się wywołać funkcji."


def normalize_purpose(value):
    if value is None:
        return None

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, dict):
        for key in ("purpose", "text", "result", "response"):
            item = value.get(key)
            if item:
                return str(item).strip()
        return str(value).strip()

    return str(value).strip()


def normalize_summaries(value):
    if value is None:
        return None

    if isinstance(value, str):
        return [{"summary": value}]

    if isinstance(value, dict):
        if "summaries" in value:
            return normalize_summaries(value["summaries"])
        return [value]

    if isinstance(value, list):
        normalized = []
        for item in value:
            if isinstance(item, dict):
                normalized.append(
                    {
                        "number": item.get("number"),
                        "title": item.get("title"),
                        "display": item.get("display"),
                        "summary": item.get("summary")
                        or item.get("content")
                        or item.get("text"),
                    }
                )
            else:
                normalized.append({"summary": str(item)})
        return normalized

    return [{"summary": str(value)}]


def analyze_thesis(pdf_path: Path) -> dict:
    result = {
        "input_file": str(pdf_path.resolve()),
        "generated_at": datetime.now().isoformat(),
        "thesis_name": pdf_path.stem,
        "purpose": None,
        "heading_summaries": None,
        "errors": {},
    }

    purpose_func, purpose_import_error = import_function(
        module_names=[
            "analysis.modules.llm.get_purpose",
        ],
        function_names=[
            "get_purpose",
            "get_purpose_details",
        ],
    )

    if purpose_func is None:
        result["errors"]["purpose_import"] = purpose_import_error
    else:
        value, err = try_call(
            purpose_func,
            ((pdf_path, "pl"), {}),
            ((pdf_path,), {}),
            ((str(pdf_path), "pl"), {}),
            ((str(pdf_path),), {}),
        )

        if err:
            result["errors"]["purpose"] = err
        else:
            result["purpose"] = normalize_purpose(value)

            if isinstance(value, dict):
                if value.get("warning"):
                    result["errors"]["purpose_warning"] = value["warning"]
                if value.get("error"):
                    result["errors"]["purpose_details"] = value["error"]

    subtitles_func, subtitles_import_error = import_function(
        module_names=[
            "analysis.modules.llm.get_subtitles",
            "analysis.modules.llm.subtitles",
            "analysis.modules.llm.extract_subtitles",
        ],
        function_names=[
            "get_subtitles",
            "extract_subtitles_from_pdf",
            "extract_and_dump_subtitles",
        ],
    )

    subtitles_value = None

    if subtitles_func is None:
        result["errors"]["subtitles_import"] = subtitles_import_error
    else:
        value, err = try_call(
            subtitles_func,
            ((pdf_path,), {}),
            ((str(pdf_path),), {}),
            ((pdf_path, "pl"), {}),
            ((str(pdf_path), "pl"), {}),
            ((pdf_path, None), {}),
        )

        if err:
            result["errors"]["subtitles"] = err
        else:
            subtitles_value = value

    summary_func, summary_import_error = import_function(
        module_names=[
            "analysis.modules.llm.get_summary",
            "analysis.modules.llm.summary",
        ],
        function_names=[
            "summarize_subtitles",
            "generate_summaries",
        ],
    )

    if summary_func is None:
        result["errors"]["summaries_import"] = summary_import_error
    else:
        value, err = try_call(
            summary_func,
            ((pdf_path,), {}),
            ((str(pdf_path),), {}),
            ((pdf_path, subtitles_value), {}),
            ((str(pdf_path), subtitles_value), {}),
            ((pdf_path, subtitles_value, "pl"), {}),
            ((str(pdf_path), subtitles_value, "pl"), {}),
        )

        if err:
            result["errors"]["summaries"] = err
        else:
            result["heading_summaries"] = normalize_summaries(value)

    return result


def save_result_txt(result: dict, pdf_path: Path) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{pdf_path.stem}_results.txt"

    lines = []
    lines.append(f"Plik: {result['input_file']}")
    lines.append(f"Wygenerowano: {result['generated_at']}")
    lines.append("")
    lines.append("NAZWA PRACY")
    lines.append(result.get("thesis_name") or pdf_path.stem)
    lines.append("")

    lines.append("CEL PRACY")
    lines.append(result["purpose"] if result["purpose"] else "Brak")
    lines.append("")

    lines.append("STRESZCZENIA NAGŁÓWKÓW")
    summaries = result.get("heading_summaries")

    if summaries:
        for item in summaries:
            display = item.get("display")
            number = item.get("number")
            title = item.get("title")
            summary = item.get("summary") or ""

            if display:
                lines.append(display)
            elif number and title:
                lines.append(f"{number} {title}")
            elif title:
                lines.append(title)
            else:
                lines.append("Sekcja")

            lines.append(summary.strip() if summary else "Brak streszczenia")
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


def main():
    pdf_path = Path(file_path)

    if not pdf_path.exists():
        print(f"Błąd: plik nie istnieje: {pdf_path}")
        return

    result = analyze_thesis(pdf_path)
    output_path = save_result_txt(result, pdf_path)

    print(f"Wynik zapisano do: {output_path}")


if __name__ == "__main__":
    main()