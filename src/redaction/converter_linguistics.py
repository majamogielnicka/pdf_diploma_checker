'''
Struktura (wraz z wieloma metodami) do mapowania surowych danych 
z ekstrakcji PDF na bardziej ustrukturyzowany format, który jest 
przyjazny dla dalszej analizy lingwistycznej i NLP.
Według moich założeń (Bartek 23.03) ta struktura nie ma otwierać na nowo pliku
lecz korzystać z wyekstraktowanej już z pdf'a struktury DocumentData (bare_struct.py).
Do poprawy lub nie ¯\_(ツ)_/¯
'''
import re
import statistics
from schema import (
    FinalDocument, ParagraphBlock, ListBlock, ListItem, 
    WordInfo, VisualElement, FloatingElements, ReferenceSections,
    classify_block_content, strip_list_marker
)
from extraction_json import DocumentData, extractPDF
from schema import PageArtifact 

class PDFMapper:
    
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
    
        combined_content = " ".join(data['content'] for data in paragraph_buffer)
        combined_words = []
        for data in paragraph_buffer:
            combined_words.extend(data['words'])
    
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

        if (len(list_buffer) > 1 ):
            first_item_data = list_buffer[0]
            new_list_block = ListBlock(
                block_id=f"list_{first_item_data['block_id']}",
                items=[data['item'] for data in list_buffer],
                bbox=first_item_data['bbox'] 
            )
            
            all_bboxes = [data['bbox'] for data in list_buffer]
            new_list_block.bbox = [
                min(b[0] for b in all_bboxes),
                min(b[1] for b in all_bboxes),
                max(b[2] for b in all_bboxes),
                max(b[3] for b in all_bboxes)
            ]
            logical_blocks.append(new_list_block)
        
        else:
            data = list_buffer[0]
            if data['item'].marker_type == "number_with_dot":
                logical_blocks.append(ParagraphBlock(
                    block_id=data['block_id'],
                    content=data['item'].text,
                    words=data['words'] 
                ))
            else:
                new_list_block = ListBlock(
                    block_id=f"list_{data['block_id']}",
                    items=[data['item']],
                    bbox=data['bbox']
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

                for line in block.lines:
                    # 1. Wyliczamy medianę przerw dla bieżącej linii
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
                            full_text += " "
                            
                            # Sprawdzamy, czy nie jesteśmy po znaku interpunkcyjnym
                            after_punct = full_text.strip().endswith(('.', '!', '?', ':', ';'))
                            
                            # Jeśli przerwa jest duża (np. > 1.8 mediany) i nie po kropce -> druga spacja
                            if current_gap > 1.8 * m_gap and not after_punct:
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
                    
                    if not full_text.endswith(" "):
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
                    PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)
                    PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                    
                    new_doc.logical_blocks.append(ParagraphBlock(
                        block_id=block.block_id,
                        content=full_text,
                        words=words_info,
                        type=current_type
                    ))
                    continue
                
                if PDFMapper.is_header(words_info):
                    PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)
                    PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                    
                    new_doc.logical_blocks.append(ParagraphBlock(
                        block_id=block.block_id,
                        content=full_text,
                        words=words_info,
                        type="heading" 
                    ))
                    continue

                block_type, marker_type = classify_block_content(full_text) # Klasyfikacja jako lista lup paragraf (początkowa, później sprawdzana ilość elementów)

                block_type, marker_type = classify_block_content(full_text)

                if block_type == "list":
                    PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)
                    cleaned_text = strip_list_marker(full_text, marker_type)
                    list_buffer.append({
                        'item': ListItem(item_id=block.block_id, marker_type=marker_type, text=cleaned_text, bbox=list(block.bbox)),
                        'words': words_info,
                        'block_id': block.block_id,
                        'bbox': list(block.bbox),
                        'original_text': full_text
                    })
                elif list_buffer and PDFMapper.is_continuation(list_buffer[-1]['bbox'], list(block.bbox)):
                    last_item = list_buffer[-1]
                    last_item['item'].text += " " + full_text
                    last_item['words'].extend(words_info)
                    
                    b = list(block.bbox)
                    last_item['bbox'] = [
                        min(last_item['bbox'][0], b[0]),
                        min(last_item['bbox'][1], b[1]),
                        max(last_item['bbox'][2], b[2]),
                        max(last_item['bbox'][3], b[3])
                    ]
                else:
                    PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                    paragraph_buffer.append({
                        'content': full_text,
                        'words': words_info,
                        'block_id': block.block_id
                    })

                    

            PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
            PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer)

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

        return new_doc