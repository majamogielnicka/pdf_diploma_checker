import sys
import traceback
import importlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[4]
SRC_DIR = PROJECT_ROOT / "src"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

from models import ModuleResult

try:
    from analysis.modules.llm.similarity import compute_similarity_for_summaries
except Exception:
    from similarity import compute_similarity_for_summaries


class LLMService:
    def __init__(self, language="pl"):
        self.language = language

    def analyze(self, processed_document):
        pdf_path = self._extract_pdf_path(processed_document)

        if not pdf_path:
            return ModuleResult(
                module_name="llm",
                status="error",
                comments=["Brak ścieżki PDF w processed_document."],
                details={"errors": {"pdf_path": "Nie znaleziono source_pdf_path/pdf_path/input_file."}},
            )

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            return ModuleResult(
                module_name="llm",
                status="error",
                comments=[f"Plik PDF nie istnieje: {pdf_path}"],
                details={"errors": {"pdf_path": f"Nie znaleziono pliku: {pdf_path}"}},
            )

        result = {
            "input_file": str(pdf_path.resolve()),
            "thesis_name": pdf_path.stem,
            "purpose": None,
            "heading_summaries": None,
            "average_similarity": None,
            "errors": {},
        }

        purpose_func, purpose_import_error = self.import_function(
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
            value, err = self.try_call(
                purpose_func,
                ((pdf_path, self.language), {}),
                ((pdf_path,), {}),
                ((str(pdf_path), self.language), {}),
                ((str(pdf_path),), {}),
            )

            if err:
                result["errors"]["purpose"] = err
            else:
                result["purpose"] = self.normalize_purpose(value)

        summary_func, summary_import_error = self.import_function(
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
            value, err = self.try_call(
                summary_func,
                ((pdf_path, None, self.language), {}),
                ((str(pdf_path), None, self.language), {}),
                ((pdf_path,), {}),
                ((str(pdf_path),), {}),
            )

            if err:
                result["errors"]["summaries"] = err
            else:
                result["heading_summaries"] = self.normalize_summaries(value)

        if result["purpose"] and result["heading_summaries"]:
            try:
                similarity_result = compute_similarity_for_summaries(
                    result["purpose"],
                    result["heading_summaries"]
                )
                result["heading_summaries"] = similarity_result["items"]
                result["average_similarity"] = similarity_result["average_similarity"]
            except Exception as e:
                result["errors"]["similarity"] = f"{type(e).__name__}: {e}"

        status = "done" if not result["errors"] else "partial"
        comments = []

        if result["purpose"]:
            comments.append("Cel pracy został wyznaczony.")
        else:
            comments.append("Nie udało się wyznaczyć celu pracy.")

        if result["heading_summaries"]:
            comments.append("Streszczenia rozdziałów zostały wygenerowane.")
        else:
            comments.append("Nie udało się wygenerować streszczeń rozdziałów.")

        if result["average_similarity"] is not None:
            comments.append(
                f"Średnie podobieństwo celu pracy do streszczeń: {result['average_similarity']:.4f}"
            )

        if result["errors"]:
            comments.append(f"Liczba błędów w module LLM: {len(result['errors'])}")

        return ModuleResult(
            module_name="llm",
            status=status,
            score=result["average_similarity"],
            comments=comments,
            details=result,
        )

    def _extract_pdf_path(self, processed_document):
        if not isinstance(processed_document, dict):
            return None

        direct_keys = [
            "source_pdf_path",
            "pdf_path",
            "input_file",
            "file_path",
        ]

        for key in direct_keys:
            value = processed_document.get(key)
            if value:
                return value

        metadata = processed_document.get("metadata")
        if isinstance(metadata, dict):
            for key in direct_keys:
                value = metadata.get(key)
                if value:
                    return value

        return None

    def import_function(self, module_names, function_names):
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

    def try_call(self, func, *variants):
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

    def normalize_purpose(self, value):
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

    def normalize_summaries(self, value):
        if value is None:
            return None

        if isinstance(value, str):
            return [{"summary": value}]

        if isinstance(value, dict):
            if "summaries" in value:
                return self.normalize_summaries(value["summaries"])
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
                            "content": item.get("content"),
                            "summary": item.get("summary")
                            or item.get("content")
                            or item.get("text"),
                        }
                    )
                else:
                    normalized.append({"summary": str(item)})
            return normalized

        return [{"summary": str(value)}]