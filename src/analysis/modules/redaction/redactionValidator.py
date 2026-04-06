'''
Znajduje się tu główna klasa RedactionValidator, która zajmuje się
...walidowaniem...
pdf'a pod względem błędów z redakcji i "zaawansowanej" redakcji.

'''

from bare_struct import DocumentData

class RedactionValidator:
    def __init__(self, document_data: DocumentData):
        self.document_data = document_data

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