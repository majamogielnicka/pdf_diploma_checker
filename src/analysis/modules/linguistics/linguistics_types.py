'''
Definicje dataclasses używanych w module lingwistycznym.
'''
from dataclasses import dataclass, field
from src.analysis.extraction.schema import ParagraphBlock, ListBlock, ListItem, BibItem, Bibliography
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
    item: str
    authors: Optional[str] = None
    date: Optional[str] = None
    title: Optional[str] = None
    is_title_italics: bool = False
    book_title: Optional[str] = None
    pages: Optional[str] = None
    publisher: Optional[str] = None
    doi: Optional[str] = None
    volume: Optional[str] = None
    access_date: Optional[str] = None
    url: Optional[str] = None
    online: bool = False
    journal: Optional[str] = None
    issue: Optional[str] = None
    entry_type: Optional[str] = None
    other: Optional[str] = None
    bibtex_type: Optional[str] = None
    author_format: Optional[str] = None
    separator: Optional[str] = None
    potential_title: Optional[str] = None

@dataclass
class Bibliography_context:
    block_id: int
    items: List[Bib_item_context] = field(default_factory=list)
    dominant_separator: Optional[str] = None
    dominant_author_format: Optional[str] = None
    dominant_language: Optional[str] = None
    dominant_marker_type: Optional[str] = None