'''
Definicje dataclasses używanych w module lingwistycznym.
'''
from dataclasses import dataclass, field
from src.analysis.extraction.schema import ParagraphBlock, ListBlock, BibItem, Bibliography
from typing import Union, List, Optional
@dataclass
class Error_type:
    content: str
    category: str
    message: str
    offset: int
    error_length: int
    block_id: int
    page_start: int
    page_end: int
    word_idxs: list[int]
    error_coordinate: list[dict]

@dataclass
class Analisys_type:
    active_ratio: str
    passive_ratio: str
    verbless_ratio: str

@dataclass
class Block_context:
    contents: str
    language: str
    block: Union[ParagraphBlock, ListBlock]

@dataclass 
class Bib_item_context:
    content: str
    authors: str
    date: str
    title: str
    is_title_italics: bool
    book_title: Optional[str]
    pages: Optional[str]
    publisher: Optional[str]
    doi: Optional[str]
    volume: Optional[str]
    access_date: Optional[str]
    url: Optional[str]
    online: Optional[bool]
    journal: Optional[str]
    issue: Optional[str]
    entry_type: Optional[str]
    other: Optional[str]
    bibtex_type: Optional[str]
    author_format: str
    separator: str
    item: BibItem

@dataclass
class Bibliography_context:
    block_id: int
    items: List[Bib_item_context] = field(default_factory=list)
    dominant_separator: Optional[str] = None
    dominant_author_format: Optional[str] = None
    dominant_language: Optional[str] = None
    dominant_marker_type: Optional[str] = None