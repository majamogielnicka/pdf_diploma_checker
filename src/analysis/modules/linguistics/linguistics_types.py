from dataclasses import dataclass
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