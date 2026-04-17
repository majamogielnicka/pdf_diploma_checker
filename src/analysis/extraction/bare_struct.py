'''
W tym pliku znajduje się cała struktura danych z pdf'a. Używamy jej do przechowywania
danych bez większego formatownia (np. bez rozdzielania na akapity, itd.), jest to tzw. 
"bare structure", która jest potem używana do dalszej analizy i redakcji. Ta struktura jest 
pierwszym krokiem do analizy dokumentu.
Przechowuje informacje o lokalizacji każdego słowa (słowa są indeksowane unikalnym span_id), czcionce, rozmiarze, kolorze, itd.
'''

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
import json

#uzywam dekoratora dataclass bo:
#ma fajne automatyczne funkcje jak tworzenie __init__ automatycznie
#jest duzo bardziej czytelny (#team_c++)
#ma wbudowana funkcje asdict() (potem sie przyda do jsona)
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

#moja propozycja:   ~Bartek 08.03
#jesli chodzi o zdjecia to wydaje mi sie ze najlepiej bedzie trzymac tylko sciezke zamiast calego obrazu zeby bylo czytelniej
#wszystkie obrazy z pdf'a beda ekstraktowane do folderu /images

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
    margins: Dict[str, float] #tego nie ma w pdf, ale bedzie funkcja ktora sama liczy przy ekstrakcji pdfa
    text_blocks: List[TextBlock] = field(default_factory=list)
    images: List[ImageInfo] = field(default_factory=list)
    tables: List[TableInfo] = field(default_factory=list)
    is_blank: bool = False


@dataclass
class DocumentData:
    metadata: Dict[str, Any]
    pages: List[PageData] = field(default_factory=list)

    def _to_dict(self):  #zeby latwo bylo przeniesc do jsona
        return asdict(self)
    
    def to_json(self, file_path: str, indent: int = 4) -> None:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._to_dict(), f, ensure_ascii=False, indent=indent)
            
        except Exception as e:
            #TODO: tutaj tez jakis wyjatek, trzeba ustalic standard zglaszania bledow
            print(f"blad zapisu do pliku json: {e}")

    def get_page_count(self) -> int:
        return len(self.pages)
    
    #zwraca słownik z nazwami czcionek i ich ilością wystąpień
    def get_font_usage(self) -> Dict[str, int]: 
        font_usage = {}
        for page in self.pages:
            for block in page.text_blocks:
                for line in block.lines:
                    for span in line.spans:
                        font_usage[span.font] = font_usage.get(span.font, 0) + 1
        return font_usage
    
    #zwraca słownik z rozmiarami czcionek i ich ilością wystąpień
    def get_font_size_usage(self) -> Dict[float, int]: 
        font_usage = {}
        for page in self.pages:
            for block in page.text_blocks:
                for line in block.lines:
                    for span in line.spans:
                        font_usage[span.size] = font_usage.get(span.size, 0) + 1
        return font_usage
    
    def get_margins(self) -> Dict[str, float]:
        margins = {}
        for page in self.pages:
            margins[page.number] = page.margins
        return margins

    def get_page_dimensions(self) -> Dict[int, tuple]:
        dimensions = {}
        for page in self.pages:
            dimensions[page.number] = (page.width, page.height)
        return dimensions
    
    def get_dominant_line_spacing(self) -> float | None:
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
    
    '''Zwraca span o danym span_id wraz z line, block i page do których span należy'''
    def get_span_by_id(self, span_id: int) -> tuple | None:
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
