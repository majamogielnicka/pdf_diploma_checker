import os
import sys
import gc
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

EXTRACTION_DIR = os.path.join(BASE_DIR, "analysis", "extraction")
COMMON_DIR     = os.path.join(BASE_DIR, "common")
LINGUISTICS_DIR = os.path.join(BASE_DIR, "analysis", "modules", "linguistics")
LLM_DIR         = os.path.join(BASE_DIR, "analysis", "modules", "llm")
REDACTION_DIR   = os.path.join(BASE_DIR, "analysis", "modules", "redaction")

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
            details={"page_count": doc_obj.get_page_count()}
        )
        

        def task_llm():
            if not use_llm:
                return None, None, "Tryb Szybki."
            
            try:
                from analysis.extraction.extraction_json import get_raster_figure_numbers
                from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
                from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
                from analysis.modules.llm.get_grade import get_overall_grade, get_content_grade
                from analysis.modules.llm.get_purpose import get_purpose
                from analysis.modules.llm.goal_realization import check_goal_realization, get_score_from_goal_result
                from analysis.modules.llm.get_summary import get_summaries
                from analysis.modules.llm.get_subtitles import get_subtitles
                from analysis.modules.llm.run_sota import get_final_sota_report
                from analysis.modules.llm.config import THESIS_PATH, LANGUAGE, MODEL_PATH, LLAVA_MMPROJ_PATH, LLAVA_MODEL_PATH
                from analysis.modules.llm.image_analysis.run_image import analyze_images
                from analysis.extraction.converter_linguistics_clean import PDFMapper
                from analysis.modules.llm.image_analysis.image_quality_checker import get_full_image_quality_json
                from analysis.modules.llm.image_analysis.font_checker import get_font_consistency_report

                mapper = PDFMapper()
                mapped_doc = mapper.map_to_schema(doc_obj)
                plain_txt_purpose = get_plain_text(pdf_path)
                txt_for_llm = extractPDF_llm(pdf_path)
                purpose = get_purpose(plain_txt_purpose, language)
                goal_result = check_goal_realization(plain_txt_purpose, purpose, language)
                purpose_score = get_score_from_goal_result(goal_result)
                purpose_reason = str(goal_result.get("reason", "") or "")
                subtitles = get_subtitles(txt_for_llm)
                summaries = get_summaries(subtitles, language)

                content_res = get_content_grade(purpose, summaries)
                if isinstance(content_res, tuple) and len(content_res) == 2:
                    content_grade_val, off_topic_headings = content_res
                else:
                    content_grade_val = content_res if isinstance(content_res, (int, float)) else 0.0
                    off_topic_headings = []

                raster_figure_numbers = get_raster_figure_numbers(doc_obj)
                raw_image_report = analyze_images(doc_obj, mapped_doc)

                total_images = len(raw_image_report)
                bad_images_count = 0
                image_details_lines = []

                for item in raw_image_report:
                    img_id = item.get("obrazek", item.get("id", "Nieznany"))
                    is_correct = item.get("poprawnosc_danych", "True")
                    errors = item.get("bledy", "None")

                    if isinstance(errors, list):
                        errors = " ".join(errors)

                    if is_correct == "False" or is_correct is False:
                        bad_images_count += 1
                        status_text = "Wykryto rozbieznosci"
                    else:
                        status_text = "Poprawny"

                    image_details_lines.append(f"Rysunek {img_id}: {status_text} - Szczegoly: {errors}")

                image_summary_data = {
                    "total": total_images,
                    "bad_count": bad_images_count,
                    "good_count": total_images - bad_images_count,
                    "details": image_details_lines,
                    "raster_numbers": raster_figure_numbers
                }
                
                quality_errors = get_full_image_quality_json(doc_obj, mapped_doc, pdf_path, verbose=False)
                font_errors = get_font_consistency_report(doc_obj, mapped_doc, verbose=False)
                
                cleanup_text_llm_instances()

                try:
                    res_id, res_title, res_score, res_method, res_cites, r1, r2, r3 = get_final_sota_report(mapped_doc, language)
                except Exception as sota_err:
                    res_id, res_title, res_score, res_method, res_cites, r1, r2, r3 = (
                        None,
                        None,
                        0,
                        "Błąd SOTA",
                        0,
                        False,
                        False,
                        False,
                    )

                score = get_overall_grade(purpose_score, content_grade_val, res_score)
                
                total_sections = len(summaries) if summaries else 1
                bad_sections = len(off_topic_headings)
                p_off_val = (bad_sections / total_sections) * 100.0 if total_sections > 0 else 0.0

                content_grade_dict = {
                    "grade": round(score, 2),
                    "max_grade": 100.0,
                    "off_topic_sections": bad_sections,
                    "p_off": round(p_off_val, 2),
                    "off_topic_headings": off_topic_headings
                }

                result = {
                    "id": res_id,
                    "tytul": res_title,
                    "ocena": res_score,
                    "podstawa": res_method,
                    "cytowania": res_cites,
                    "r1": r1,
                    "r2": r2,
                    "r3": r3,
                    "content_grade": content_grade_dict,
                    "image_analysis": image_summary_data,
                    "jakosc_obrazkow": quality_errors,
                    "czcionki_obrazkow": font_errors
                }

                return result, score, "Analiza LLM zakończona pomyślnie."
            
            except Exception as e:
                return None, None, "Błąd analizy SOTA/LLM."
        def task_linguistics():
            try:
                from analysis.extraction.extraction_json import extractPDF
                from analysis.extraction.converter_linguistics_clean import PDFMapper
                import importlib.util
                mapper = PDFMapper()
                ling_path = os.path.join(LINGUISTICS_DIR, "run_linguistics.py")
                spec = importlib.util.spec_from_file_location("analysis.modules.linguistics.run_linguistics", ling_path)
                ling_module = importlib.util.module_from_spec(spec)
                ling_module.__package__ = "analysis.modules.linguistics"
                sys.modules["analysis.modules.linguistics.run_linguistics"] = ling_module
                spec.loader.exec_module(ling_module)
                
                raw_blocks = mapper.map_to_schema(doc_obj)
                for block in raw_blocks.logical_blocks:
                    block.language = language
                ling_matches, sentence_analysis = ling_module.run_linguistics(raw_blocks)
                stats = {
                    "active_ratio": getattr(sentence_analysis, "active_ratio", "0%"),
                    "passive_ratio": getattr(sentence_analysis, "passive_ratio", "0%"),
                    "verbless_ratio": getattr(sentence_analysis, "verbless_ratio", "0%")
                }
                return ling_matches, stats
            except Exception as e:
                import traceback
                traceback.print_exc()
                return [], {"active_ratio": "0%", "passive_ratio": "0%", "verbless_ratio": "0%"}

                
        def task_redaction():
            try:
                from analysis.modules.redaction.redaction_validator import RedactionValidator
                from analysis.extraction.converter_linguistics_clean import PDFMapper
                mapper = PDFMapper()
                validator = RedactionValidator(
                    document_data=doc_obj, 
                    document_data_linguistics=mapper.map_to_schema(doc_obj), 
                    config_path=config_path
                )
                
                font_usage = doc_obj.get_font_size_usage()
                doc_obj.get_most_common_font_size = lambda: max(font_usage, key=font_usage.get, default=12) if font_usage else 12
                
                redaction_errors = validator.validate()
                return redaction_errors
            except Exception as e:
                import traceback
                traceback.print_exc()
                return []
        report_progress(30, "Rozpoczynam analizy...")

        redaction_errors = task_redaction()
        report_progress(50, "Redakcja zakończona. Uruchamiam pozostałe analizy...")

        ling_matches, ling_stats = task_linguistics()

        if use_llm:
            llm_result, content_grade_result, llm_summary_text = task_llm()
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
                f"Znaleziono {len(wszystkie_bledy)} błędów do wyświetlenia na ekranie."
            ],
            recommendations=[]
        )
        if final_report.llm_result is None:
            final_report.llm_result = {}
        final_report.llm_result["statystyki_zdan"] = ling_stats

        final_report.linguistics_errors = wszystkie_bledy
        
        return final_report