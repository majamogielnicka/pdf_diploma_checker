'''
Definicje dataclasses używanych w module lingwistycznym.
'''
from dataclasses import dataclass, field
from analysis.extraction.schema import ParagraphBlock, ListBlock
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
    authors: Optional[dict[str, str]] = None
    date: Optional[list[dict[str, str]]] = None
    title: Optional[dict[str, str]] = None
    is_title_italics: bool = False
    book_title: Optional[dict[str, str]] = None
    pages: Optional[dict[str, str]] = None
    publisher: Optional[dict[str, str]] = None
    doi: Optional[dict[str, str]] = None
    volume: Optional[dict[str, str]] = None
    access_date: Optional[dict[str, str]] = None
    url: Optional[dict[str, str]] = None
    online: bool = False
    journal: Optional[dict[str, str]] = None
    issue: Optional[dict[str, str]] = None
    entry_type: Optional[str] = None
    other: Optional[str] = None
    bibtex_type: Optional[str] = None
    separator: Optional[str] = None

@dataclass
class Bibliography_context:
    block_id: int
    items: List[Bib_item_context] = field(default_factory=list)