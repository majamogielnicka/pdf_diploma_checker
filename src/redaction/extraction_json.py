from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
import os
import fitz  # PyMuPDF
import json
from pathlib import Path

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
    image_type: str 

@dataclass
class TableInfo:
    bbox: tuple
    row_count: int
    col_count: int
    data: List[List[str]] 

@dataclass
class PageData:
    number: int
    width: float
    height: float
    margins: Dict[str, float] #tego nie ma w pdf, ale bedzie funkcja ktora sama liczy przy ekstrakcji pdfa
    text_blocks: List[TextBlock] = field(default_factory=list)
    images: List[ImageInfo] = field(default_factory=list)
    tables: List[TableInfo] = field(default_factory=list)

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
    
def fix_latex(text):
    replace = { #Słownik znaków do podmiany.
        "´s": "ś",
        "´S": "Ś",
        "´c": "ć",
        "´C": "Ć",
        "´z": "ź",
        "´Z": "Ź",
        "˙z": "ż",
        "˙Z": "Ż",
        "´n": "ń",
        "´N": "Ń",
        "´o": "ó",
        "´O": "Ó",
    }
    for wrong, right in replace.items():
        text = text.replace(wrong, right)
    return text

def extract_tables(page: fitz.Page, drawings: list, cur_page: PageData) -> list:
    table_bboxes = []
    #TODO: znajdywanie tabel typu APA czyli, takich z niestandardowym obramowaniem bez linii poziomych albo jakichkolwiek linii. ogólna poprawa działania funkcji
    #znajdowanie tabel, wyciąganie danych i zapisywanie do list
    tabs = page.find_tables(strategy="lines_strict") 
    for tab in tabs.tables:
        extracted_data = tab.extract() # Wyciąga dane jako List[List[str]]

        #zabezpieczenie przed zapisywaniem przypadkowo znalezionych elemetów które są z zasady za małe by być tabelami
        if tab.col_count < 2: 
            continue
        if tab.row_count == 2 and tab.col_count == 2:
            continue
        
        is_flowchart = False
        for d in drawings:
            d_rect = fitz.Rect(d["rect"])

            if d_rect.intersects(tab.bbox):
                for item in d["items"]:

                    if item[0] == "l":
                        p1, p2 = item[1], item[2]

                        if abs(p1.x - p2.x) > 1 and abs(p1.y - p2.y) > 1:
                            is_flowchart = True
                            break
                    elif item[0] in ("c", "q"): 
                        is_flowchart = True
                        break
            if is_flowchart:
                break

        if is_flowchart:
            continue
        #usuwa entery i zamienia na spacje, można potem usunąć jakbyśmy chcieli widzieć gdzie są entery
        cleaned_data = [ 
            [cell.replace('\n', ' ').strip() if cell else "" for cell in row]
            for row in extracted_data
        ]

        #zabezpieczenie przed zapisywaniem wykresów jako tabelek
        total_cells = tab.row_count * tab.col_count 
        if total_cells > 0:
            filled_cells = sum(1 for row in cleaned_data for cell in row if cell != "")
            fill_ratio = filled_cells / total_cells
            
            if fill_ratio < 0.40:
                continue        
        
        total_chars = sum(len(cell) for row in cleaned_data for cell in row)
        if total_chars > 0:
            max_chars_in_cell = max(len(cell) for row in cleaned_data for cell in row)
            
            if max_chars_in_cell / total_chars > 0.80:
                continue

        avg_chars_per_cell = total_chars / filled_cells
        if fill_ratio < 0.55 and avg_chars_per_cell < 15:
            continue 
            
        
        table_bboxes.append(fitz.Rect(tab.bbox))
        cur_page.tables.append(TableInfo(
            bbox=tab.bbox,
            row_count=tab.row_count,
            col_count=tab.col_count,
            data=cleaned_data
        ))      

    return table_bboxes

def extract_vector_graphics(page: fitz.Page, drawings: list, page_index: int, table_bboxes: list, cur_page: PageData) -> None:
    if not drawings:
        return

    vector_bboxes = []
    for d in drawings:
       
       # tutaj jest zakomentowane zabezpieczenie przed zapisywaniem podpisów typu "Praca własna", 
       # które są na szarym tle i są uznawane za grafikę wektorową
       # Póki co nwm czy to dobrze czy to źle ale jak źle to można odkomentować 
       # PS. nie testowane na wszystkich pdf bo to trwa i trwa
       # ~Maciej, 17.03
       '''
       color = d.get("color")
       fill = d.get("fill")
       
       is_invisible = False

       if color is None and fill is None:
           is_invisible = True

       elif color is None and fill is not None:
           if len(fill) in (1, 3) and min(fill) >= 0.98: 
               is_invisible = True
           elif len(fill) == 4 and max(fill) <= 0.02: 
               is_invisible = True
               
       if is_invisible:
           continue
       '''
       rect = d["rect"]
       if max(rect.width, rect.height) > 2:
           vector_bboxes.append(fitz.Rect(rect))
    
    merged_bboxes = vector_bboxes.copy()
    changed = True
    
    while changed:
        changed = False
        new_merged = []
        
        while len(merged_bboxes) > 0:
            current = merged_bboxes.pop(0)
            expanded_current = current + (-50, -50, 50, 50)
            
            i = 0
            while i < len(merged_bboxes):
                if expanded_current.intersects(merged_bboxes[i]):
                    current = current | merged_bboxes[i]
                    expanded_current = current + (-50, -50, 50, 50)
                    merged_bboxes.pop(i)
                    changed = True
                else:
                    i += 1
            new_merged.append(current)
        merged_bboxes = new_merged

    MIN_PHYSICAL_WIDTH = 40
    MIN_PHYSICAL_HEIGHT = 20
    
    for i, bbox in enumerate(merged_bboxes):
        if bbox.width > MIN_PHYSICAL_WIDTH and bbox.height > MIN_PHYSICAL_HEIGHT:
            aspect_ratio = bbox.width / bbox.height
            
            if aspect_ratio < 15.0 and aspect_ratio > 0.1:
                
                is_invalid = False
                
                for t_bbox in table_bboxes:
                    intersect = bbox & t_bbox 
                    if intersect.is_valid and not intersect.is_empty:
                        overlap_area = intersect.width * intersect.height
                        bbox_area = bbox.width * bbox.height
                        if bbox_area > 0 and (overlap_area / bbox_area) > 0.15:
                            is_invalid = True
                            break
                                
                if is_invalid:
                    continue

                pix = page.get_pixmap(clip=bbox)
                img_path = f"images/p{page_index}_vec_{i}.png"
                pix.save(img_path)
                
                cur_page.images.append(ImageInfo(
                    path=img_path,
                    bbox=(bbox.x0, bbox.y0, bbox.x1, bbox.y1),
                    width=pix.width,
                    height=pix.height,
                    image_type="vector"
                ))

def extractPDF(file_path: str) -> DocumentData:
    if not os.path.exists(file_path):
        #TODO:tutaj jakis wyjatek
        #musimy ustalić standard zglaszania bledow
        #na razie print
        #   ~Bartek 08.03
        print(f"plik nie istnieje")
        return
    
    #sprawdzenie czy mamy folder "images", jeśli nie to tworzymy taki
    os.makedirs("images", exist_ok=True)

    #usuwanie obrazów z poprzedniego sprawdzania, żeby nie było chaosu
    for filename in os.listdir("images"):
        file_to_delete = os.path.join("images", filename)
        try:
            if os.path.isfile(file_to_delete):
                os.remove(file_to_delete)
        except Exception as e:
            print(f"Nie udało się usunąć starego pliku {file_to_delete}: {e}")
    
    #TODO: dalsza walidacja
    doc = fitz.open(file_path)
    metadata = doc.metadata
    document_data = DocumentData(metadata=metadata)

    for page_index, page in enumerate(doc):
        raw_dict = page.get_text("dict")
        word_list = page.get_text("words")
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

        drawings = page.get_drawings()

        table_bboxes = extract_tables(page, drawings, cur_page)

        for block in raw_dict["blocks"]:
            #typ 0 to tekst, typ 1 to obraz
            #TODO: rozroznianie obrazow rastrowych i wektorowych
            if block["type"] == 0:
                text_block = _parse_text_block(block, word_list)
                if text_block.lines:
                    cur_page.text_blocks.append(text_block)
            
            elif block["type"] == 1:
                x0, y0, x1, y1 = block["bbox"]
                phys_width = x1 - x0
                phys_height = y1 - y0
                
                MIN_PHYSICAL_WIDTH = 20
                MIN_PHYSICAL_HEIGHT = 20
                
                if phys_width < MIN_PHYSICAL_WIDTH or phys_height < MIN_PHYSICAL_HEIGHT:
                    continue

                if phys_height > 0:
                    aspect_ratio = phys_width / phys_height
                    if aspect_ratio > 15.0 or aspect_ratio < 0.15:
                        continue
                
                ext = block.get("ext", "png")
                img_path = f"images/p{page_index}_b{block['number']}.{ext}"

                #zapisywanie obrazów
                with open(img_path, "wb") as img_file:
                    img_file.write(block["image"])
                cur_page.images.append(ImageInfo(
                    path=img_path,
                    bbox=block["bbox"],
                    width=block["width"],
                    height=block["height"],
                    image_type="raster"
                ))

        extract_vector_graphics(page, drawings, page_index, table_bboxes, cur_page)      

        document_data.pages.append(cur_page)

    doc.close()
    return document_data

#Niestety używanie samego dicta powoduje, że nie można dokładnie rozdzielić spanów na same słowa z informacją
#o ich położeniu. Natomiast sama lista słów zwraca dokładne koordynaty słowa, ale nie pozwala na 
#detekcję czcionki, itd. W związku z tym użyto zarówno dicta jak i listy słów, aby połączyć korzyści.
def _parse_text_block(raw_block: dict, word_list:list) -> TextBlock:
    lines = []
    block_words = []

    #Sprawdzanie, które słowa są w środk danego bloku, żeby nie sprawdzać każdego słowa
    #na stronie czy nie należy do danego spana

    for x in word_list:
        if x[5] == raw_block["number"]:
            block_words.append(x)

    for raw_line in raw_block["lines"]:
        spans = []
        for raw_span in raw_line["spans"]:
            if not raw_span["text"].strip():
                continue
            
            s_bbox = raw_span["bbox"]
            span_words = []

            for x in block_words:
                #Sprawdzanie czy dane słowo należy do spanu z małym marginesem błędu (0.2), w razie
                #problemów można zwiększyć
                if (x[0] >= s_bbox[0] - 0.2 and x[1]>= s_bbox[1]-0.2 and x[2]<=s_bbox[2]+0.2 and x[3]<=s_bbox[3]+0.2): 
                    span_words.append(x)

            #obsluga flag
            flags = raw_span["flags"]

            if span_words:
                for x in span_words:
                    spans.append(TextSpan(
                        text=fix_latex(x[4]),
                        font=raw_span["font"],
                        size=round(raw_span["size"], 2),
                        color=raw_span["color"],
                        bold=bool(flags & 16),
                        italic=bool(flags & 2),
                        bbox=(x[0],x[1],x[2],x[3])
                    ))
            else:
                spans.append(TextSpan(
                    text=fix_latex(raw_span["text"]),
                    font=raw_span["font"],
                    size=round(raw_span["size"], 2),
                    color=raw_span["color"],                        bold=bool(flags & 16),
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

pdf_path = Path("src/theses/ch.pdf")
doc_data = extractPDF(pdf_path) 

#TODO: dodac warunek sprqwdzjaacy blad do testow
doc_data.to_json("output.json") 

#data_as_dictionary = doc_data.to_dict() # Konwersja na słownik
#
#with open("output.json", "w", encoding="utf-8") as f: # Zapis do pliku .json
#    json.dump(data_as_dictionary, f, indent=4, ensure_ascii=False)