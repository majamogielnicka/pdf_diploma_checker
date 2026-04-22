from models import InputDocument
from pipeline import AnalysisPipeline

def run_analysis_for_pdf(pdf_path, language="pl", config_path=None, progress_callback=None, use_llm=True):
    if not pdf_path:
        raise ValueError("Nie podano ścieżki do pliku PDF.")

    input_document = InputDocument(
        pdf_path=pdf_path,
        language=language,
        config_path=config_path
    )

    pipeline = AnalysisPipeline()
    return pipeline.run(input_document, progress_callback=progress_callback, use_llm=use_llm)