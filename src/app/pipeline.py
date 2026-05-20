import os
import sys
import concurrent.futures
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

    def run(self, input_document, progress_callback=None, use_llm=True, config_path=None):
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
                from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
                from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
                from analysis.modules.llm.get_grade import get_overall_grade, get_content_grade, get_purpose_grade
                from analysis.modules.llm.get_purpose import get_purpose
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
                raw_image_report = analyze_images(doc_obj, mapped_doc)
                plain_txt_purpose = get_plain_text(pdf_path)
                txt_for_llm = extractPDF_llm(pdf_path)

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
                    "details": image_details_lines
                }

                language = "pl"
                purpose = get_purpose(plain_txt_purpose, language)
                subtitles = get_subtitles(txt_for_llm)
                summaries = get_summaries(subtitles, language)

                content_res = get_content_grade(purpose, summaries)
                if isinstance(content_res, tuple) and len(content_res) == 2:
                    content_grade_val, off_topic_headings = content_res
                else:
                    content_grade_val = content_res if isinstance(content_res, (int, float)) else 0.0
                    off_topic_headings = []

                purpose_res = get_purpose_grade(txt_for_llm, purpose, language)
                if isinstance(purpose_res, tuple) and len(purpose_res) == 2:
                    purpose_score, purpose_reason = purpose_res
                else:
                    purpose_score = purpose_res if isinstance(purpose_res, (int, float)) else 0
                    purpose_reason = "Brak uzasadnienia (błąd lub limit czasu CPU)"
                
                quality_errors = get_full_image_quality_json(doc_obj, mapped_doc, pdf_path, verbose=False)
                font_errors = get_font_consistency_report(doc_obj, mapped_doc, verbose=False)
                
                res_id, res_title, res_score, res_method, res_cites, r1, r2, r3 = get_final_sota_report(mapped_doc, language)
        
                score = get_overall_grade(purpose_score, content_grade_val, res_score)
                
                total_sections = len(summaries) if summaries else 1
                bad_sections = len(off_topic_headings)
                p_off_val = (bad_sections / total_sections) * 100.0 if total_sections > 0 else 0.0

                content_grade_dict = {
                    "grade": round(score, 2),
                    "max_grade": 100.0,
                    "off_topic_sections": bad_sections,
                    "p_off": round(p_off_val, 2),
                    "off_topic_headings": off_topic_headings,
                    "purpose_reason": purpose_reason
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
                print(f"[PIPELINE] Błąd skryptu LLM/SOTA: {e}")
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
                ling_matches, sentence_analysis = ling_module.run_linguistics(raw_blocks, config_path)
                print(f"[PIPELINE] Znaleziono {len(ling_matches)} błędów lingwistycznych.")
                return ling_matches
            except Exception as e:
                print(f"[PIPELINE] Błąd lingwistyki: {e}")
                import traceback
                traceback.print_exc()
                return []
                
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
                print(f"[PIPELINE] Znaleziono {len(redaction_errors)} błędów redakcyjnych.")
                return redaction_errors
            except Exception as e:
                print(f"[PIPELINE] Błąd analizy redakcyjnej: {e}")
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

            ling_matches = future_ling.result()

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
                f"Znaleziono {len(wszystkie_bledy)} błędów do wyświetlenia na ekranie."
            ],
            recommendations=[]
        )
        
        final_report.linguistics_errors = wszystkie_bledy
        
        return final_report