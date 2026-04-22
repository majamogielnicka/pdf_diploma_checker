import os
import sys
import concurrent.futures

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXTRACTION_DIR = os.path.join(BASE_DIR, "analysis", "extraction")
COMMON_DIR = os.path.join(BASE_DIR, "common")
LINGUISTICS_DIR = os.path.join(BASE_DIR, "analysis", "modules", "linguistics")
LLM_DIR = os.path.join(BASE_DIR, "analysis", "modules", "llm")
REDACTION_DIR = os.path.join(BASE_DIR, "analysis", "modules", "redaction")

for path in [BASE_DIR, EXTRACTION_DIR, COMMON_DIR, LINGUISTICS_DIR, LLM_DIR, REDACTION_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from service import ExtractionService
from linguistics_service import LinguisticsService
from models import FinalReport, ModuleResult

class AnalysisPipeline:
    def __init__(self):
        self.extraction_service = ExtractionService()
        self.linguistics_service = LinguisticsService()
        self.llm_service = None

    def run(self, input_document, progress_callback=None, use_llm=True):
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
        
        if use_llm:
            report_progress(35, "Trwa analiza SOTA (State of the Art)...")
            try:
                from run_sota import get_final_sota_report
                
                s_id, s_title, s_score, s_method, s_cites, r1, r2, r3 = get_final_sota_report(pdf_path)
                
                llm_result = {
                    "id": s_id,
                    "tytul": s_title,
                    "ocena": s_score,
                    "podstawa": s_method,
                    "cytowania": s_cites,
                    "r1": r1,
                    "r2": r2,
                    "r3": r3
                }
                report_progress(75, "Szukanie błędów językowych...")

                llm_summary_text = f"Analiza SOTA wykonana (Wynik: {s_score}%)."
            except Exception as e:
                print(f"[PIPELINE] Błąd skryptu SOTA: {e}")
                llm_result = None
                llm_summary_text = "Błąd analizy SOTA."
        else:
            llm_result = None
            report_progress(40, "Tryb Szybki - pominięto analizę SOTA...")
            llm_summary_text = "Analiza SOTA została POMINIĘTA (Tryb Szybki)."

            report_progress(75, "Szukanie błędów językowych...")
        try:
            import importlib.util
            ling_path = os.path.join(LINGUISTICS_DIR, "run_mock_data.py")
            spec = importlib.util.spec_from_file_location("analysis.modules.linguistics.run_mock_data", ling_path)
            ling_module = importlib.util.module_from_spec(spec)
            ling_module.__package__ = "analysis.modules.linguistics"
            sys.modules["analysis.modules.linguistics.run_mock_data"] = ling_module
            spec.loader.exec_module(ling_module)
            from analysis.extraction.converter_linguistics import PDFMapper
            raw_blocks = PDFMapper.map_to_schema(doc_obj)
            
            ling_matches = ling_module.run_linguistics(raw_blocks)
            print(f"[PIPELINE] Znaleziono {len(ling_matches)} błędów lingwistycznych.")
            
        except Exception as e:
            print(f"[PIPELINE] Błąd nowej lingwistyki: {e}")
            import traceback
            traceback.print_exc()
            ling_matches = []
        report_progress(85, "Trwa sprawdzanie błędów redakcyjnych...")
        try:
            from analysis.modules.redaction.redaction_validator import RedactionValidator
            class DummyLinguistics:
                def __init__(self): self.logical_blocks = []
            validator = RedactionValidator(document_data=doc_obj, document_data_linguistics=DummyLinguistics())
            redaction_errors = validator.validate()
            print(f"[PIPELINE] Znaleziono {len(redaction_errors)} błędów redakcyjnych.")
        except Exception as e:
            print(f"[PIPELINE] Błąd analizy redakcyjnej: {e}")
            import traceback
            traceback.print_exc()
            redaction_errors = []

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