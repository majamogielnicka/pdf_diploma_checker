'''
W tym pliku mamy całą strukturę danych z pdf'a podzieloną logicznie.
'''
from dataclasses import dataclass, field, asdict
import json
from typing import List, Dict, Any, Union, Optional
import re # Regular Expressions - manipulacja tekstem za pomocą wzorców

### ------ @DATACLASSES DLA LINGWISTYKI ------ ###
@dataclass
class WordInfo: # Położenie XY oraz relatywne słowa
    word_index: int
    text: str
    start_char: int    
    end_char: int      
    font: str
    size: float
    bold: bool
    italic: bool
    bbox: List[float]
    page_number: int
    
@dataclass
class HeadingInfo: # Informacje o nagłówkach (TODO)
    level: int
    number: str
    text: str

@dataclass
class ParagraphBlock: # Informacje o blokach tekstowych, które mogą być paragrafami, nagłówkami lub listami
    block_id: Union[int, str]
    type: str = "paragraph"
    content: str = ""
    words: List[WordInfo] = field(default_factory=list)
    headings: List[HeadingInfo] = field(default_factory=list)

@dataclass
class ListItem:
    item_id: int
    marker_type: str
    text: str
    bbox: List[float]
    words: List[WordInfo] = field(default_factory=list)

@dataclass
class ListBlock:
    block_id: Union[int, str]
    content: str
    words: List[WordInfo]
    items: List[ListItem]
    bbox: List[float]
    type: str = "list"

@dataclass
class PageArtifact: # Informacje o elementach pływających, takich jak numery stron, nagłówki/stopki, itp.
    artifact_id: int
    type: str  # np. "page_number"
    page_number: int
    text: str
    bbox: List[float]

@dataclass
class Footnote: # Informacje o przypisach (TODO)
    footnote_id: int
    page_number: int
    marker: str
    text: str
    bbox: List[float]

@dataclass
class VisualElement: # Informacje o elementach wizualnych, takich jak wykresy, rysunki, tabele itp.
    element_id: int
    type: str  # "figure" lub "table"
    page_number: int
    bbox: List[float]
    caption: Dict[str, Any] # text, label_type, number, description, bbox
    table_data: Optional[List[List[str]]] = None
    format: Optional[Dict[str, int]] = None # num_rows, num_columns

@dataclass
class Equation: # Informacje o równaniach, zarówno w tekście, jak i jako elementy pływające (TODO)
    equation_id: int
    page_number: int
    type: str = "block_equation"
    text: str = ""
    bbox: List[float] = field(default_factory=list)

@dataclass
class BibItem: # Informacje o elementach bibliografii (TODO)
    item_id: str
    marker_text: str
    full_text: str
    bbox: List[float]
    words: List[WordInfo]

@dataclass
class Bibliography: # Informacje o sekcji bibliografii (TODO)
    list_id: str
    page_number: int
    items: List[BibItem]

@dataclass
class TOCItem: # Informacje o elementach spisu treści (TODO)
    item_id: str
    level: int
    number: str
    text: str
    full_text: str
    target_page: int
    bbox: List[float]

@dataclass
class CodeSnippet: # Informacje o fragmentach kodu (w tekście i jako elementy pływające) (TODO)
    snippet_id: int
    page_number: int
    language: str
    text: str
    bbox: List[float]


@dataclass
class FloatingElements: # Informacje o wszystkich elementach pływających na stronie
    page_artifacts: List[PageArtifact] = field(default_factory=list)
    footnotes: List[Footnote] = field(default_factory=list)
    visual_elements: List[VisualElement] = field(default_factory=list)
    equations: List[Equation] = field(default_factory=list)

@dataclass
class ReferenceSections: # Informacje o wszystkich sekcjach referencyjnych (TODO)
    bibliography: List[Bibliography] = field(default_factory=list)
    table_of_contents: List[TOCItem] = field(default_factory=list)
    code_snippets: List[CodeSnippet] = field(default_factory=list)

@dataclass
class FinalDocument: # Ostateczna struktura dokumentu
    metadata: Dict[str, Any]
    logical_blocks: List[Union[ParagraphBlock, ListBlock]] = field(default_factory=list)
    floating_elements: FloatingElements = field(default_factory=list)
    reference_sections: ReferenceSections = field(default_factory=list)

    def to_json(self, file_path: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=4)

# Słownik wzorców dla list
LIST_PATTERNS = {
    "number_with_dot": r"^\d+(\.\d+)*\.\s",
    "number_with_bracket": r"^\d+\)\s?",
    "letter_with_dot": r"^[a-z]\.\s",
    "letter_with_bracket": r"^[a-z]\)\s?",
    "bullet": r"^[••●○■]",
    "dash": r"^[-\u2013\u2014]"
}
HEADER_PATTERN = r"^\d+(\.\d+)*\s+"  # Wykrywa 1.1, 1.2.1 itd.
CAPTION_PATTERN = r"^(Tabela|Tab|Rysunek|Rys|Wykres|Fig|Figure)\s+\d+"
TOC_DOTS_PATTERN = r"\.{4,}" # Wykrywa ciągi kropek w spisie treści

# Klasyfikacja typu bloku (paragraf lub lista) na podstawie tego czy zaczyna się od typowych elementów dla listy
def classify_block_content(text: str):
    text = text.strip()
    for marker_type, pattern in LIST_PATTERNS.items():
        if re.match(pattern, text, re.IGNORECASE):
            return "list", marker_type
    return "paragraph", None

# Usunięcie markera z początku pozycji na liście
def strip_list_marker(text: str, marker_type: str) -> str:
    if marker_type in LIST_PATTERNS:
        return re.sub(LIST_PATTERNS[marker_type], "", text, count=1).strip()
    return text.strip()
