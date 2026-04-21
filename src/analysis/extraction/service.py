from src.analysis.extraction.extraction_json import extractPDF


class ExtractionService:
    def process(self, input_document):
        document_data = extractPDF(input_document.pdf_path)

        if document_data is None:
            raise ValueError("Ekstrakcja PDF nie zwróciła danych.")

        return document_data._to_dict()