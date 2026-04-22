'''
Struktura błędu wykrytego podczas analizy. Zawiera wszystkie informacje według template.json.
'''

from dataclasses import dataclass

class Module:
    REDACTION = "redaction"
    LINGUISTIC = "linguistic"
    LLM = "llm"

@dataclass
class Error:
    id: str
    module: str
    category: str
    page_number: int
    bounding_box: list
    text: str
    comments: str

    def get_xy(self):
        x1, y1, _, _ = self.bounding_box
        return (x1, y1)
    
'''
Wszystkie błędy z wczytywaniem plików, walidacją plików, itd.
'''
class FileError(Error):
    pass
