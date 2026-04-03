class InputDocument:
    def __init__(self, pdf_path, language="pl", config_path=None):
        self.pdf_path = pdf_path
        self.language = language
        self.config_path = config_path

    def __repr__(self):
        return (
            f"InputDocument(pdf_path={self.pdf_path}, "
            f"language={self.language}, config_path={self.config_path})"
        )

    def to_dict(self):
        return {
            "pdf_path": self.pdf_path,
            "language": self.language,
            "config_path": self.config_path,
        }


class ModuleResult:
    def __init__(self, module_name, status, score=None, comments=None, details=None):
        self.module_name = module_name
        self.status = status
        self.score = score
        self.comments = comments if comments is not None else []
        self.details = details if details is not None else {}

    def __repr__(self):
        return (
            f"ModuleResult(module_name={self.module_name}, "
            f"status={self.status}, score={self.score})"
        )

    def to_dict(self):
        return {
            "module_name": self.module_name,
            "status": self.status,
            "score": self.score,
            "comments": self.comments,
            "details": self.details,
        }


class FinalReport:
    def __init__(
        self,
        document_name,
        processed_document=None,
        extraction_result=None,
        linguistics_result=None,
        plagiarism_result=None,
        llm_result=None,
        final_score=None,
        summary=None,
        recommendations=None,
    ):
        self.document_name = document_name
        self.processed_document = processed_document
        self.extraction_result = extraction_result
        self.linguistics_result = linguistics_result
        self.plagiarism_result = plagiarism_result
        self.llm_result = llm_result
        self.final_score = final_score
        self.summary = summary if summary is not None else []
        self.recommendations = recommendations if recommendations is not None else []

    def __repr__(self):
        return (
            f"FinalReport(document_name={self.document_name}, "
            f"final_score={self.final_score})"
        )

    def to_dict(self):
        return {
            "document_name": self.document_name,
            "processed_document": str(self.processed_document),
            "extraction_result": self.extraction_result.to_dict() if self.extraction_result else None,
            "linguistics_result": self.linguistics_result.to_dict() if self.linguistics_result else None,
            "plagiarism_result": self.plagiarism_result.to_dict() if self.plagiarism_result else None,
            "llm_result": self.llm_result.to_dict() if self.llm_result else None,
            "final_score": self.final_score,
            "summary": self.summary,
            "recommendations": self.recommendations,
        }