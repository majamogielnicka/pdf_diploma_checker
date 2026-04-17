'''
Znajduje się tu główna klasa RedactionValidator, która zajmuje się
...walidowaniem...
pdf'a pod względem błędów z redakcji i "zaawansowanej" redakcji.

'''

from src.analysis.extraction.bare_struct import DocumentData
from src.analysis.errors.error_struct import RedactionError, Module

class RedactionValidator:
    def __init__(self, document_data: DocumentData):
        self.document_data = document_data
        self.id_counter = 0

    def _get_next_id(self):
        id = f"ERR_RED_{self.id_counter}"
        self.id_counter += 1
        self.module = Module.REDACTION
        return id

    def validate(self):
        errors = []
        orphans = self.check_orphans()
        for orphan in orphans:
            error = RedactionError(
                id=self._get_next_id(),
                module=self.module,
                category="orphan",
                page_nr=orphan.page_nr,
                bounding_box=orphan.bounding_box,
                text=orphan.text,
                comments="Orphan character detected. Consider checking the redaction quality."
            )
            errors.append(error)
        blank_pages = self.check_blank_page()
        for blank_page in blank_pages:
            error = RedactionError(
                id = self._get_next_id(),
                module = self.module,
                category = "blank_page",
                page_nr = blank_page.number,
                bounding_box = None,
                text = None,
                comments = "Blank page detected. Consider checking content of this page."
            )
            errors.append(error)
        return errors

    def check_orphans(self):
        orphans = []
        conjuncions = []
        for page in self.document_data.pages:
            for block in page.text_blocks:
                for line in block.lines:
                    if line.spans is None or len(line.spans) == 0:
                        continue
                    last_span = None
                    for span in line.spans[::-1]:
                        if span.text.strip() == "":
                            continue
                        last_span = span
                        break
                    if last_span is None:
                        continue
                    if len(last_span.text) == 1:
                        if last_span.text in ".,;:!?\"')]}":
                            continue
                        orphans.append(last_span)
        return orphans
    
    def check_blank_page(self):
        blank_pages = []
        for page in self.document_data.pages:
            if page.is_blank == True:
                blank_pages.append(page)

        return blank_pages
