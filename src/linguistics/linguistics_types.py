from dataclasses import dataclass
@dataclass
class Error_type:
    category: str
    message: str
    offset: int
    error_length: int