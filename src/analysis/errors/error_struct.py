'''
Struktura błędu wykrytego podczas analizy. Zawiera wszystkie informacje według template.json.
Docelowo chciałbym, żeby była to globalna struktura dla naszego projektu, na razie umieszczam
tylko tutaj.
'''

from dataclasses import dataclass

class Module:
    REDACTION = "redaction"
    LINGUISTIC = "linguistic"
    LLM = "llm"

@dataclass
class RedactionError:
    id: str
    module: str
    category: str
    page_nr: int
    bounding_box: list
    text: str
    comments: str

    def get_xy(self):
        x1, y1, _, _ = self.bounding_box
        return (x1, y1)
