from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
import json
@dataclass
class TextSpan:
    span_id: int
    text: str
    font: str
    size: float
    color: int
    bold: bool
    italic: bool
    bbox: tuple #(x0, y0, x1, y1)

@dataclass
class TextLine:
    spans: List[TextSpan]
    bbox: tuple
    baseline: float # odleglosc od dolnej krawedzi
    alignement: str = "unknown"
    spacing_consistency: bool = True # czy równe odstępy między słowami w linijce
    # gap_to_r: float = 0.0 # debug
    line_spacing: float | None = None

@dataclass
class TextBlock:
    block_id: int
    lines: List[TextLine]
    bbox: tuple
    block_type: str = "text"

@dataclass
class TocEntry:
    level: int
    title: str
    page: int
    bbox: tuple
    src_page: int #Strona na ktorej znajduje sie czesc spisu tresci z odnosnikiem do tego naglowka

@dataclass
class TofEntry:
    number: str
    title: str
    page: int
    bbox: tuple
    src_page: int
@dataclass
class TotEntry:
    number: str
    title: str
    page: int
    bbox: tuple
    src_page: int

@dataclass
class TocData:
    page_nums: List[int]
    entries: List[TocEntry]
    text: str
@dataclass
class TofData:
    page_nums: List[int]
    entries: List[TofEntry]
    text: str
@dataclass
class TotData:
    page_nums: List[int]
    entries:List[TotEntry]
    text:str
@dataclass
class ImageInfo:
    path: str
    bbox: tuple
    width: int
    height: int
    image_type: str 
    description: str 

@dataclass
class TableInfo:
    bbox: tuple
    row_count: int
    col_count: int
    description: str
    data: List[List[str]] 
    table_type: str = "classic"

@dataclass
class PageData:
    number: int
    width: float
    height: float
    orientation: str
    format: str
    margins: Dict[str, float]
    text_blocks: List[TextBlock] = field(default_factory=list)
    images: List[ImageInfo] = field(default_factory=list)
    tables: List[TableInfo] = field(default_factory=list)
    is_blank: bool = False


@dataclass
class DocumentData:
    metadata: Dict[str, Any]
    pages: List[PageData] = field(default_factory=list)
    toc: TocData | None = None
    tof: TofData | None = None
    tot: TotData | None = None

    def _to_dict(self):
        '''This function converts the entire data structure to a dictionary, which can then be easily saved to JSON.'''
        return asdict(self)
    
    def to_json(self, file_path: str, indent: int = 4) -> None:
        '''This function saves the document data to a JSON file.'''
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._to_dict(), f, ensure_ascii=False, indent=indent)
            
        except Exception as e:
            #TODO: tutaj tez jakis wyjatek, trzeba ustalic standard zglaszania bledow
            print(f"blad zapisu do pliku json: {e}")

    def get_page_count(self) -> int:
        '''This function returns the number of pages in the document, excluding the title page.'''
        return len(self.pages) - 1 # -1, jako że strona tytułowa ma się nie zaliczać do licznika stron.
    
    #zwraca słownik z nazwami czcionek i ich ilością wystąpień
    def get_font_usage(self) -> Dict[str, int]: 
        '''This function returns a dictionary with font names as keys and their occurrence counts as values.'''
        font_usage = {}
        for page in self.pages:
            for block in page.text_blocks:
                for line in block.lines:
                    for span in line.spans:
                        font_usage[span.font] = font_usage.get(span.font, 0) + 1
        return font_usage
    
    #zwraca słownik z rozmiarami czcionek i ich ilością wystąpień
    def get_font_size_usage(self) -> Dict[float, int]: 
        '''This function returns a dictionary with font sizes as keys and their occurrence counts as values.'''
        font_usage = {}
        for page in self.pages:
            for block in page.text_blocks:
                for line in block.lines:
                    for span in line.spans:
                        font_usage[span.size] = font_usage.get(span.size, 0) + 1
        return font_usage
    
    def get_most_common_font(self) -> str | None:
        '''This function returns the most common font in the document.'''
        font_usage = self.get_font_usage()
        if not font_usage:
            return None
        most_common_font = max(font_usage, key=font_usage.get)
        return most_common_font

    def get_most_common_font_size(self) -> float | None:
        '''This function returns the most common font size in the document.'''
        font_size_usage = self.get_font_size_usage()
        if not font_size_usage:
            return None
        most_common_font_size = max(font_size_usage, key=font_size_usage.get)
        return most_common_font_size

    def get_margins(self) -> Dict[str, float]:
        '''This function returns a dictionary with page numbers as keys and their margins as values.'''
        margins = {}
        for page in self.pages:
            margins[page.number] = page.margins
        return margins

    def get_page_dimensions(self) -> Dict[int, tuple]:
        '''This function returns a dictionary with page numbers as keys and their dimensions as values.'''
        dimensions = {}
        for page in self.pages:
            dimensions[page.number] = (page.width, page.height)
        return dimensions
    
    def get_dominant_line_spacing(self) -> float | None:
        '''This function returns the most common line spacing in the document.'''
        spacing_counts = {}
        for page in self.pages:
            for block in page.text_blocks:
                for line in block.lines:
                    if line.line_spacing is not None:
                        spacing_counts[line.line_spacing] = spacing_counts.get(line.line_spacing, 0) + 1
        
        if not spacing_counts:
            return None
        
        dominant_spacing = max(spacing_counts, key=spacing_counts.get)
        return dominant_spacing
    
    def get_span_by_id(self, span_id: int) -> tuple | None:
        '''This function returns the span with the given span_id along with its associated line, block, and page.'''
        first_idx_in_page = []
        for page in self.pages:
            if page.text_blocks:
                first_idx_in_page.append(page.text_blocks[0].lines[0].spans[0].span_id)
            else:
                first_idx_in_page.append(first_idx_in_page[-1] if first_idx_in_page else 0)
        for page in self.pages:
            first = first_idx_in_page[page.number]
            last = first_idx_in_page[page.number + 1] if page.number + 1 < len(first_idx_in_page) else float('inf')
            if first <= span_id < last:
                for block in page.text_blocks:
                    for line in block.lines:
                        for span in line.spans:
                            if span.span_id == span_id:
                                return span, line, block, page 
        return None

    def is_rect_intersecting(self, rect: tuple, page: PageData, ignore: List[int] = None) -> List[tuple]:
        '''This function checks which spans intersects with the given rectangle and returns a list of those spans along with their associated lines, blocks, and pages.
        The ignore parameter can be used to specify span_ids that should be ignored during the intersection check.'''
        if ignore is None:
            ignore = []
        intersecting_spans = []
        rx0, ry0, rx1, ry1 = rect
        for block in page.text_blocks:
            for line in block.lines:
                for span in line.spans:
                    if span.span_id in ignore:
                        continue
                    sx0, sy0, sx1, sy1 = span.bbox
                
                    if rx0 <= sx1 and sx0 <= rx1 and ry0 <= sy1 and sy0 <= ry1:
                        intersecting_spans.append((span, line, block, page))
        return intersecting_spans