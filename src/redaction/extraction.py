from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
import os
import fitz  # PyMuPDF
import json

#uzywam dekoratora dataclass bo:
#ma fajne automatyczne funkcje jak tworzenie __init__ automatycznie
#jest duzo bardziej czytelny (#team_c++)
#ma wbudowana funkcje asdict() (potem sie przyda do jsona)
@dataclass
class TextSpan:
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
    baseline: float #odleglosc od dolnej krawedzi

@dataclass
class TextBlock:
    block_id: int
    lines: List[TextLine]
    bbox: tuple

#moja propozycja:   ~Bartek 08.03
#jesli chodzi o zdjecia to wydaje mi sie ze najlepiej bedzie trzymac tylko sciezke zamiast calego obrazu zeby bylo czytelniej
#wszystkie obrazy z pdf'a beda ekstraktowane do folderu /images

@dataclass
class ImageInfo:
    path: str
    bbox: tuple
    width: int
    height: int

@dataclass
class PageData:
    number: int
    width: float
    height: float
    margins: Dict[str, float] #tego nie ma w pdf, ale bedzie funkcja ktora sama liczy przy ekstrakcji pdfa
    text_blocks: List[TextBlock] = field(default_factory=list)
    images: List[ImageInfo] = field(default_factory=list)

@dataclass
class DocumentData:
    metadata: Dict[str, Any]
    pages: List[PageData] = field(default_factory=list)

    def to_dict(self):  #zeby latwo bylo przeniesc do jsona
        return asdict(self)
    
def calculate_margins(blocks, width, height) -> Dict[str, float]:
    if not blocks:
        return {"top": 0.0, "bottom": 0.0, "left": 0.0, "right": 0.0}

    # inicjalizacja marginesów do optymalizacji (początkowo lewy maksymalnie po prawej, dolny maksymalnie na górze itd)
    margin_top_buf = height # odczytane koordynaty są od góry do dołu (góra to y=0, dół to y=wysokość_dokumentu)
    margin_bottom_buf = 0   
    margin_left_buf = width
    margin_right_buf = 0

    for b in blocks: #iterowanie po rozmiarach każdego z bloczków, szukanie min/max wartości
        x0, y0, x1, y1 = b["bbox"]
        if x0 < margin_left_buf: margin_left_buf = x0
        if y0 < margin_top_buf: margin_top_buf = y0
        if x1 > margin_right_buf: margin_right_buf = x1
        if y1 > margin_bottom_buf: margin_bottom_buf = y1

    # wyznaczenie faltycznych wielkości marginesów
    margin_top = margin_top_buf
    margin_bottom = height - margin_bottom_buf
    margin_left = margin_left_buf
    margin_right = width - margin_right_buf
        
    return {
        "top": margin_top,
        "bottom": margin_bottom,
        "left": margin_left,
        "right": margin_right
    }


def extractPDF(file_path: str) -> DocumentData:
    if not os.path.exists(file_path):
        #TODO:tutaj jakis wyjatek
        #musimy ustalić standard zglaszania bledow
        #na razie print
        #   ~Bartek 08.03
        print(f"plik nie istnieje")
        return
    
    #TODO: dalsza walidacja
    doc = fitz.open(file_path)
    metadata = doc.metadata
    document_data = DocumentData(metadata=metadata)

    for page_index, page in enumerate(doc):
        raw_dict = page.get_text("dict")
        p_width = page.rect.width
        p_height = page.rect.height

        cur_page = PageData(
            number=page_index + 1,
            width=p_width,
            height=p_height,
            margins=calculate_margins(raw_dict["blocks"], p_width, p_height),
            text_blocks=[],
            images=[]
        )

        for block in raw_dict["blocks"]:
            #typ 0 to tekst, typ 1 to obraz
            #TODO: rozroznianie obrazow rastrowych i wektorowych
            if block["type"] == 0:
                text_block = _parse_text_block(block)
                if text_block.lines:
                    cur_page.text_blocks.append(text_block)
            
            elif block["type"] == 1:
                img_path = f"images/p{page_index}_b{block['number']}.png"
                #TODO: funkcja do zapisywania obrazow
                cur_page.images.append(ImageInfo(
                    path=img_path,
                    bbox=block["bbox"],
                    width=block["width"],
                    height=block["height"]
                ))

        document_data.pages.append(cur_page)

    doc.close()
    return document_data

def _parse_text_block(raw_block: dict) -> TextBlock:
    lines = []
    for raw_line in raw_block["lines"]:
        spans = []
        for raw_span in raw_line["spans"]:
            if not raw_span["text"].strip():
                continue
            
            #obsluga flag
            flags = raw_span["flags"]
            spans.append(TextSpan(
                text=raw_span["text"],
                font=raw_span["font"],
                size=round(raw_span["size"], 2),
                color=raw_span["color"],
                bold=bool(flags & 16),
                italic=bool(flags & 2),
                bbox=raw_span["bbox"]
            ))
        
        if spans:
            lines.append(TextLine(
                spans=spans,
                bbox=raw_line["bbox"],
                baseline=raw_line["wmode"]
            ))
            
    return TextBlock(lines=lines, bbox=raw_block["bbox"], block_id=raw_block["number"])

#test:
#print(extractPDF("1.pdf").to_dict())
doc_data = extractPDF("1.pdf") 
data_as_dictionary = doc_data.to_dict() # Konwersja na słownik

with open("output.json", "w", encoding="utf-8") as f: # Zapis do pliku .json
    json.dump(data_as_dictionary, f, indent=4, ensure_ascii=False)
