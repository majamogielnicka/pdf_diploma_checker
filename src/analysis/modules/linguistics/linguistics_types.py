'''
Definicje dataclasses używanych w module lingwistycznym.
'''
from dataclasses import dataclass
from analysis.extraction.schema import ParagraphBlock, ListBlock
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

