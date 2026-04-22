from dataclasses import dataclass
from src.analysis.extraction.schema import ParagraphBlock, ListBlock
from typing import Union
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
    error_coordinate: tuple

@dataclass
class Analisys_type:
    passive_count: int
    active_count: int
    impersonal_count: int
    wrong_person_count: int
    passive_ratio: str
    sentence_count: int

@dataclass
class Block_context:
    contents: str
    language: str
    block: Union[ParagraphBlock, ListBlock]

