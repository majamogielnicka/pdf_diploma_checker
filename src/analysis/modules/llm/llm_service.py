from models import ModuleResult


class LLMService:
    def analyze(self, processed_document):
        pages = processed_document.get("pages", [])

        return ModuleResult(
            module_name="llm",
            status="done",
            comments=["Analiza LLM została uruchomiona poprawnie."],
            details={
                "page_count_seen_by_llm": len(pages)
            }
        )