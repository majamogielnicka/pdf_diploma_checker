import os
import sys
import concurrent.futures

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

EXTRACTION_DIR = os.path.join(BASE_DIR, "analysis", "extraction")
COMMON_DIR = os.path.join(BASE_DIR, "common")
LINGUISTICS_DIR = os.path.join(BASE_DIR, "analysis", "modules", "linguistics")
LLM_DIR = os.path.join(BASE_DIR, "analysis", "modules", "llm")
REDACTION_DIR = os.path.join(BASE_DIR, "analysis", "modules", "redaction")

from common.path import resource_path
from analysis.modules.linguistics import run_mock_data as ling_module

for path in [BASE_DIR, EXTRACTION_DIR, COMMON_DIR, LINGUISTICS_DIR, LLM_DIR, REDACTION_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from analysis.extraction.service import ExtractionService
from analysis.modules.linguistics.linguistics_service import LinguisticsService
from common.models import FinalReport, ModuleResult


class AnalysisPipeline:
    def __init__(self):
        self.extraction_service = ExtractionService()
        self.linguistics_service = LinguisticsService()
        self.llm_service = None

    def run(self, input_document, progress_callback=None, use_llm=True, config_path=None, language="pl"):
        def cleanup_text_llm_instances():
            """Zwalnia instancje LLM z modułów tekstowych, by ograniczyć użycie VRAM przed SOTA."""
            try:
                from analysis.modules.llm import get_summary as _get_summary_mod
                from analysis.modules.llm import goal_realization as _goal_realization_mod
                from analysis.modules.llm import get_purpose as _get_purpose_mod

                llm_obj = getattr(_get_summary_mod, "_LLM", None)
                if llm_obj is not None:
                    close_fn = getattr(llm_obj, "close", None)
                    if callable(close_fn):
                        close_fn()
                    _get_summary_mod._LLM = None

                llm_obj = getattr(_goal_realization_mod, "_LLM", None)
                if llm_obj is not None:
                    close_fn = getattr(llm_obj, "close", None)
                    if callable(close_fn):
                        close_fn()
                    _goal_realization_mod._LLM = None

                model_cache = getattr(_get_purpose_mod, "_LLAMA_MODELS", None)
                if isinstance(model_cache, dict):
                    for model in list(model_cache.values()):
                        close_fn = getattr(model, "close", None)
                        if callable(close_fn):
                            close_fn()
                    model_cache.clear()
            except Exception:
                pass

            gc.collect()

        def report_progress(value, text):
            if progress_callback:
                progress_callback(value, text)

        if input_document is None:
            raise ValueError("Nie przekazano dokumentu wejściowego.")

        pdf_path = getattr(input_document, "pdf_path", None)

        if not pdf_path or not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Nie znaleziono pliku: {pdf_path}")

        report_progress(10, "Rozpoczynam ekstrakcję tekstu z PDF...")

        from analysis.extraction.extraction_json import extractPDF

        doc_obj = extractPDF(pdf_path)
        doc_dict = doc_obj._to_dict()

        extraction_result = ModuleResult(
            module_name="extraction",
            status="done",
            comments=["Ekstrakcja dokumentu zakończona poprawnie."],
            details={"page_count": doc_obj.get_page_count()},
        )

        def task_llm():
            try:
                from llm_task import run_task_llm

                return run_task_llm(
                    doc_obj=doc_obj,
                    pdf_path=pdf_path,
                    language=language,
                    use_llm=use_llm,
                )

            except Exception as e:
                print(f"[PIPELINE] Błąd skryptu LLM: {e}")
                import traceback
                traceback.print_exc()
                return None, None, "Błąd analizy LLM."

        def task_linguistics():
            try:
                from analysis.extraction.converter_linguistics_clean import PDFMapper
                import importlib.util

                mapper = PDFMapper()

                ling_path = os.path.join(LINGUISTICS_DIR, "run_linguistics.py")
                spec = importlib.util.spec_from_file_location(
                    "analysis.modules.linguistics.run_linguistics",
                    ling_path,
                )
                ling_module = importlib.util.module_from_spec(spec)
                ling_module.__package__ = "analysis.modules.linguistics"
                sys.modules["analysis.modules.linguistics.run_linguistics"] = ling_module
                spec.loader.exec_module(ling_module)

                raw_blocks = mapper.map_to_schema(doc_obj)

                for block in raw_blocks.logical_blocks:
                    block.language = language

                ling_matches, sentence_analysis = ling_module.run_linguistics(raw_blocks)

                print(f"[PIPELINE] Znaleziono {len(ling_matches)} błędów lingwistycznych.")

                stats = {
                    "active_ratio": getattr(sentence_analysis, "active_ratio", "0%"),
                    "passive_ratio": getattr(sentence_analysis, "passive_ratio", "0%"),
                    "verbless_ratio": getattr(sentence_analysis, "verbless_ratio", "0%"),
                }

                return ling_matches, stats

            except Exception as e:
                import traceback
                traceback.print_exc()

                return [], {
                    "active_ratio": "0%",
                    "passive_ratio": "0%",
                    "verbless_ratio": "0%",
                }

        def task_redaction():
            try:
                from analysis.modules.redaction.redaction_validator import RedactionValidator
                from analysis.extraction.converter_linguistics_clean import PDFMapper

                mapper = PDFMapper()

                validator = RedactionValidator(
                    document_data=doc_obj,
                    document_data_linguistics=mapper.map_to_schema(doc_obj),
                    config_path=config_path,
                )

                font_usage = doc_obj.get_font_size_usage()
                doc_obj.get_most_common_font_size = (
                    lambda: max(font_usage, key=font_usage.get, default=12)
                    if font_usage
                    else 12
                )

                redaction_errors = validator.validate()

                print(f"[PIPELINE] Znaleziono {len(redaction_errors)} błędów redakcyjnych.")

                return redaction_errors

            except Exception as e:
                import traceback
                traceback.print_exc()

                return []

        report_progress(30, "Rozpoczynam analizy...")

        redaction_errors = task_redaction()

        report_progress(50, "Redakcja zakończona. Uruchamiam pozostałe analizy...")

        workers_count = 2 if use_llm else 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers_count) as executor:
            future_ling = executor.submit(task_linguistics)

            if use_llm:
                future_llm = executor.submit(task_llm)

            ling_matches, ling_stats = future_ling.result()

            if use_llm:
                llm_result, content_grade_result, llm_summary_text = future_llm.result()
            else:
                llm_result = None
                content_grade_result = None
                llm_summary_text = "Analiza LLM została pominięta."

        report_progress(100, "Generowanie raportu końcowego...")

        wszystkie_bledy = ling_matches + redaction_errors

        final_report = FinalReport(
            document_name=os.path.basename(pdf_path),
            processed_document=doc_dict,
            extraction_result=extraction_result,
            llm_result=llm_result,
            summary=[
                "Ekstrakcja zakończona.",
                "Analiza językowa zakończona.",
                "Analiza redakcyjna zakończona.",
                llm_summary_text,
                f"Znaleziono {len(wszystkie_bledy)} błędów do wyświetlenia na ekranie.",
            ],
            recommendations=[],
        )

        if final_report.llm_result is None:
            final_report.llm_result = {}

        final_report.llm_result["statystyki_zdan"] = ling_stats
        final_report.linguistics_errors = wszystkie_bledy

        return final_report