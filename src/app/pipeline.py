import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXTRACTION_DIR = os.path.join(BASE_DIR, "analysis", "extraction")
COMMON_DIR = os.path.join(BASE_DIR, "common")
LINGUISTICS_DIR = os.path.join(BASE_DIR, "analysis", "modules", "linguistics")
LLM_DIR = os.path.join(BASE_DIR, "analysis", "modules", "llm")

for path in [EXTRACTION_DIR, COMMON_DIR, LINGUISTICS_DIR, LLM_DIR]:
    if path not in sys.path:
        sys.path.append(path)

from service import ExtractionService
from linguistics_service import LinguisticsService
from llm_service import LLMService
from models import FinalReport, ModuleResult


class AnalysisPipeline:
    def __init__(self):
        self.extraction_service = ExtractionService()
        self.linguistics_service = LinguisticsService()
        self.llm_service = LLMService()

    def run(self, input_document):
        if input_document is None:
            raise ValueError("Nie przekazano dokumentu wejściowego.")

        pdf_path = getattr(input_document, "pdf_path", None)

        if not pdf_path:
            raise ValueError("Brak ścieżki PDF w obiekcie InputDocument.")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Nie znaleziono pliku: {pdf_path}")

        processed_document = self.extraction_service.process(input_document)

        print("[PIPELINE] Ekstrakcja wykonana poprawnie.")
        print(f"[PIPELINE] Liczba stron po ekstrakcji: {len(processed_document.get('pages', []))}")

        extraction_result = ModuleResult(
            module_name="extraction",
            status="done",
            comments=["Ekstrakcja dokumentu zakończona poprawnie."],
            details={
                "page_count": len(processed_document.get("pages", []))
            }
        )

        linguistics_result = self.linguistics_service.analyze(processed_document)
        llm_result = self.llm_service.analyze(processed_document)

        return FinalReport(
            document_name=os.path.basename(pdf_path),
            processed_document=processed_document,
            extraction_result=extraction_result,
            linguistics_result=linguistics_result,
            llm_result=llm_result,
            summary=[
                "Ekstrakcja została wykonana.",
                "Analiza językowa została wykonana.",
                "Analiza LLM została wykonana."
            ],
            recommendations=[]
        )