'''
Struktura (wraz z wieloma metodami) do mapowania surowych danych 
z ekstrakcji PDF na bardziej ustrukturyzowany format, który jest 
przyjazny dla dalszej analizy lingwistycznej i NLP.
'''
import re
import statistics

from .schema_llm import (
    FinalDocument, ParagraphBlock, ListBlock, ListItem, 
    WordInfo, VisualElement, FloatingElements, ReferenceSections,
    classify_block_content, strip_list_marker
)
from .extraction_json_llm import DocumentData, extractPDF_llm, calculate_margins
from .schema_llm import PageArtifact 

#### wersja temporary, jutro sprawdz 
class PDFMapper_llm:
    
    # Sprawdznie, czyy kolejny blok należy do danego podpunktu listy
    @staticmethod
    def is_continuation(last_item_bbox: list, current_block_bbox: list) -> bool:
        last_x0 = last_item_bbox[0]
        curr_x0 = current_block_bbox[0]
        return abs(last_x0 - curr_x0) < 10 or curr_x0 > last_x0
    
    # Heurystyczne sprawdzenie czy coś jest nagłówkiem
    @staticmethod
    def is_header(words: list[WordInfo]) -> bool:
        if not words: return False
        
        is_bold = all(w.bold for w in words)
        is_italic = all(w.italic for w in words)
        avg_size = sum(w.size for w in words) / len(words)
        
        return (is_bold and len(words) < 15) or (is_italic and len(words) < 15) or avg_size > 12.5
    
    # Mergowanie linijek w spójne akapity
    @staticmethod
    def empty_paragraph_buffer(logical_blocks, paragraph_buffer):
        if not paragraph_buffer:
            return

        combined_content = ""
        combined_words = []
        current_offset = 0

        for i, data in enumerate(paragraph_buffer):
            content = data['content']

            # Oblicz separator (spacja lub brak, jeśli łącznik)
            separator = ""
            if i > 0:
                if not combined_content.rstrip().endswith('-'):
                    separator = " "

            for word in data['words']:
                shift = current_offset + len(separator)
                combined_words.append(WordInfo(
                    word_index=len(combined_words),  # globalny, unikalny indeks
                    text=word.text,
                    start_char=word.start_char + shift,
                    end_char=word.end_char + shift,
                    font=word.font,
                    size=word.size,
                    bold=word.bold,
                    italic=word.italic,
                    bbox=word.bbox,
                    page_number=word.page_number
                ))

            combined_content += separator + content
            current_offset = len(combined_content)

        logical_blocks.append(ParagraphBlock(
            block_id=paragraph_buffer[0]['block_id'],
            content=combined_content,
            words=combined_words
        ))
        paragraph_buffer.clear()

    @staticmethod
    # Opróznianie bufora listy:
    # Zapis całości jako lista jeśli więcej niż jeden element,
    # Zapis jako paragraf jeśli tylko jeden element
    def empty_list_buffer(logical_blocks, list_buffer): 
        if not list_buffer:
            return
        
        items = [data['item'] for data in list_buffer]
        all_words = []
        for item in items:
            all_words.extend(item.words)
            
        combined_content = "\n".join(item.text for item in items)

        if (len(items) > 1):
            first_item_data = list_buffer[0]
            new_list_block = ListBlock(
                block_id=f"list_{first_item_data['block_id']}",
                content=combined_content,
                words=all_words,
                items=items,
                bbox=first_item_data['bbox'] 
            )
            
            all_bboxes = [item.bbox for item in items]
            new_list_block.bbox = [
                min(b[0] for b in all_bboxes),
                min(b[1] for b in all_bboxes),
                max(b[2] for b in all_bboxes),
                max(b[3] for b in all_bboxes)
            ]
            logical_blocks.append(new_list_block)
        
        else:
            data = list_buffer[0]
            item = data['item']
            if item.marker_type == "number_with_dot":
                logical_blocks.append(ParagraphBlock(
                    block_id=data['block_id'],
                    content=item.text,
                    words=item.words 
                ))
            else:
                new_list_block = ListBlock(
                    block_id=f"list_{data['block_id']}",
                    content=item.text,
                    words=item.words,
                    items=[item],
                    bbox=item.bbox
                )
                logical_blocks.append(new_list_block)
        
        list_buffer.clear()

    @staticmethod
    def map_to_schema(old_doc: DocumentData) -> FinalDocument:
        new_doc = FinalDocument(
            metadata=old_doc.metadata,
            floating_elements=FloatingElements(),
            reference_sections=ReferenceSections()
        )

        list_buffer = [] 
        paragraph_buffer = []

        for page in old_doc.pages:
            top_thresh = 50
            bottom_thresh = page.height - 50

            page_table_descs = {t.description for t in page.tables if t.description}
            page_img_descs = {img.description for img in page.images if img.description}

            margins = calculate_margins(
                [{"bbox": b.bbox} for b in page.text_blocks], 
                page.width, 
                page.height
            )
            x0_margin = margins["left"]            
            margin_indent_thresh = 7.5

            for block in page.text_blocks:
                full_text = ""
                words_info = []
                word_counter = 0

                temp_text = "".join(s.text for l in block.lines for s in l.spans).strip().lower()
                
                x0, y0, x1, y1 = block.bbox

                # Uproszczone sprawdzanie artefaktów na dole i górze strony 
                if (y1 < top_thresh or y0 > bottom_thresh):
                    
                    new_artifact = PageArtifact(
                        artifact_id=block.block_id,
                        type="nr strony (tymczasowo uproszczone)", #TODO: rozbudować klasyfikację artefaktów
                        page_number=page.number,
                        text=temp_text,
                        bbox=list(block.bbox)
                    )
                    new_doc.floating_elements.page_artifacts.append(new_artifact)
                    
                    continue

                last_y1 = None

                for line in block.lines:
                    # Lewy koordynat x linii (do sprawdzenia, czy nowy akapit)
                    line_x0 = line.spans[0].bbox[0] if line.spans else block.bbox[0]
                    line_x1 = line.spans[-1].bbox[2] if line.spans else block.bbox[2]

                    
                    # Sprawdzanie, czy nowy akapit jeśli za duża różnica w pionie między linijkami
                    current_y0 = line.spans[0].bbox[1] if line.spans else line.bbox[1]
                    current_y1 = line.spans[-1].bbox[3] if line.spans else line.bbox[3]
    
                    if last_y1 is not None:
                        vertical_gap = current_y0 - last_y1
                        line_height = current_y1 - current_y0
                        if vertical_gap > line_height * 1.5:
                            PDFMapper_llm.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)
                    
                    last_y1 = current_y1
                    
                    if paragraph_buffer and (line_x0 > x0_margin + margin_indent_thresh):
                        PDFMapper_llm.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)

                    # Wyliczenie mediany przerw dla bieżącej linii (do wykrycia podwójnych spacji)
                    line_gaps = []
                    for i in range(len(line.spans) - 1):
                        g = line.spans[i+1].bbox[0] - line.spans[i].bbox[2]
                        if g > 0: line_gaps.append(g)
                    
                    # Mediana pozwala zignorować ekstremalne rozciągnięcia przy justowaniu
                    m_gap = statistics.median(line_gaps) if line_gaps else 3.0
                    
                    prev_span_x1 = None
                    for span in line.spans:
                        word_text = span.text.replace('\u200b', '').strip()
                        if not word_text: continue
                        
                        if prev_span_x1 is not None:
                            current_gap = span.bbox[0] - prev_span_x1
                            
                            # Zawsze dodajemy bazową spację, bo extraction_json wycina wszystko
                            if not (full_text.rstrip().endswith('-') and abs(line_x1 - span.bbox[2]) < 50):
                                full_text += " "
                            
                                # Sprawdzenie, czy nie jesteśmy po znaku interpunkcyjnym
                                after_punct = full_text.strip().endswith(('.', '!', '?', ':', ';'))
                            
                                # Jeśli przerwa jest duża (np. > 1.2 mediany) i nie po kropce -> druga spacja
                                if current_gap > 1.2 * m_gap and not after_punct:
                                    full_text += " "
                                # Jeśli przerwa jeszcze większa (np. > 1.5 mediany) i po kropce -> druga spacja
                                if current_gap > 1.5 * m_gap and after_punct:
                                    full_text += " "

                        start_char = len(full_text)
                        words_info.append(WordInfo(
                            word_index=word_counter,
                            text=word_text,
                            start_char=start_char,
                            end_char=start_char + len(word_text),
                            font=span.font,
                            size=span.size,
                            bold=span.bold,
                            italic=span.italic,
                            bbox=list(span.bbox),
                            page_number=page.number
                        ))
                        
                        full_text += word_text
                        prev_span_x1 = span.bbox[2]
                        word_counter += 1
                    
                    if not full_text.endswith(" ") and not full_text.rstrip().endswith("-"):
                        full_text += " "
                
                full_text = full_text.strip()
                if not full_text: continue
                if len(full_text) < 2: 
                    continue
                
                normalized_text = re.sub(r'\s+', ' ', full_text).strip()
                clean_table_descs = {re.sub(r'\s+', ' ', d).strip() for d in page_table_descs}
                clean_img_descs = {re.sub(r'\s+', ' ', d).strip() for d in page_img_descs}

                current_type = None
                if normalized_text in clean_table_descs:
                    current_type = "table_description"
                elif normalized_text in clean_img_descs:
                    current_type = "img_decription"

                if current_type:
                    PDFMapper_llm.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)
                    PDFMapper_llm.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                    
                    new_doc.logical_blocks.append(ParagraphBlock(
                        block_id=block.block_id,
                        content=full_text,
                        words=words_info,
                        type=current_type
                    ))
                    continue
                
                if PDFMapper_llm.is_header(words_info):
                    PDFMapper_llm.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)
                    PDFMapper_llm.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                    
                    new_doc.logical_blocks.append(ParagraphBlock(
                        block_id=block.block_id,
                        content=full_text,
                        words=words_info,
                        type="heading" 
                    ))
                    continue

                block_type, marker_type = classify_block_content(full_text)

                if block_type == "list":
                    PDFMapper_llm.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)
                    cleaned_text = strip_list_marker(full_text, marker_type)
                    list_buffer.append({
                        'item': ListItem(
                            item_id=block.block_id, 
                            marker_type=marker_type, 
                            text=cleaned_text, 
                            bbox=list(block.bbox),
                            words=words_info
                        ),
                        'words': words_info,
                        'block_id': block.block_id,
                        'bbox': list(block.bbox),
                        'original_text': full_text
                    })
                elif list_buffer and PDFMapper_llm.is_continuation(list_buffer[-1]['bbox'], list(block.bbox)):
                    last_item_data = list_buffer[-1]
                    connector = "" if last_item_data['item'].text.rstrip().endswith('-') else " "
                    last_item_data['item'].text += connector + full_text
                    last_item_data['item'].words.extend(words_info)
                    
                    b = list(block.bbox)
                    last_item_data['item'].bbox = [
                        min(last_item_data['item'].bbox[0], b[0]),
                        min(last_item_data['item'].bbox[1], b[1]),
                        max(last_item_data['item'].bbox[2], b[2]),
                        max(last_item_data['item'].bbox[3], b[3])
                    ]
                    # Synchronizacja bbox w słowniku bufora
                    last_item_data['bbox'] = last_item_data['item'].bbox
                else:
                    PDFMapper_llm.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                    paragraph_buffer.append({
                        'content': full_text,
                        'words': words_info,
                        'block_id': block.block_id
                    })

            for table in page.tables: # Mapowanie tabel jako elementów pływających
                ve = VisualElement(
                    element_id=id(table),
                    type="table",
                    page_number=page.number,
                    bbox=list(table.bbox),
                    caption={"text": table.description},
                    table_data=table.data,
                    format={"num_rows": table.row_count, "num_columns": table.col_count}
                )
                new_doc.floating_elements.visual_elements.append(ve)

        # Opróżnianie buforów dopiero po przetworzeniu wszystkich stron, by uniknąć urywania akapitów
        PDFMapper_llm.empty_list_buffer(new_doc.logical_blocks, list_buffer)
        PDFMapper_llm.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)

        return new_doc

MULTISPACE_RE = re.compile(r"\s+")


def clean_ws(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")
    return MULTISPACE_RE.sub(" ", text).strip()


def get_plain_text(pdf_path):
    raw_doc = extractPDF_llm(str(pdf_path))
    mapped_doc = PDFMapper_llm.map_to_schema(raw_doc)

    parts = []

    for block in mapped_doc.logical_blocks:
        block_type = getattr(block, "type", None)
        text = clean_ws(getattr(block, "content", "") or "")

        if not text:
            continue

        if block_type in {"list", "table_description", "img_decription"}:
            continue

        parts.append(text)

    return clean_ws(" ".join(parts))
