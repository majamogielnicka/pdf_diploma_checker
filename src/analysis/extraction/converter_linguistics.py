'''
Struktura (wraz z wieloma metodami) do mapowania surowych danych 
z ekstrakcji PDF na bardziej ustrukturyzowany format, który jest 
przyjazny dla dalszej analizy lingwistycznej i NLP.
'''
import re
import statistics
import fitz  # PyMuPDF
from typing import Dict

from src.analysis.extraction.schema import (
    FinalDocument, ParagraphBlock, ListBlock, ListItem, 
    WordInfo, VisualElement, FloatingElements, ReferenceSections,
    classify_block_content, strip_list_marker
)
from src.analysis.extraction.extraction_json import DocumentData, extractPDF, calculate_margins
from src.analysis.extraction.schema import PageArtifact, is_acronym, find_table_description, find_image_description 
# Klasa mapowania danych do formatu odpowiedniego dla lingwistyki
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
    @staticmethod
    def is_keywords(words: list[WordInfo]) -> bool:
        if not words: return False

        full_text = " ".join(w.text for w in words).strip()

        if full_text.lower().startswith(("słowa kluczowe", "keywords", "key words", "keywords:", "skróty")):
            return True
        return False
    
    # Sprawdzenie, czy dany blok nalezy do tabeli, w celu uniknięcia dubloiwania elementów
    @staticmethod
    def is_inside_table(block_bbox: list, table_bboxes: list) -> bool:
        bx0, by0, bx1, by1 = block_bbox
        block_area = (bx1 - bx0) * (by1 - by0)
        
        if block_area <= 0: 
            return False

        for tx0, ty0, tx1, ty1 in table_bboxes:
            ix0 = max(bx0, tx0 - 5)
            iy0 = max(by0, ty0 - 5)
            ix1 = min(bx1, tx1 + 5)
            iy1 = min(by1, ty1 + 5)

            if ix0 < ix1 and iy0 < iy1:
                intersect_area = (ix1 - ix0) * (iy1 - iy0)
                if intersect_area / block_area > 0.8: 
                    return True
        return False

    
    # Mergowanie linijek w spójne akapity
    @staticmethod
    def empty_paragraph_buffer(logical_blocks, paragraph_buffer, debug_why_empty = ""):
        if not paragraph_buffer:
            return

        import re
        
        # Detekcja akronimów:
        is_acronym_block = False
        total_lines = len(paragraph_buffer)

        is_widow = 0
        is_bekart = 0
        is_szewc = 0

        # Wykrywanie blokow z akronimami, jeśli zlepione w jedną linijkę
        if total_lines == 1:
            content = paragraph_buffer[0]['content'].strip()

            # Regex dla wykrywania bloków z akronimami            
            starts_with_sep = bool(re.match(r'^\S{1,15}\s*[-–—−‐:=]\s+', content))
            starts_with_upper = bool(re.match(r'^[A-ZĄĆĘŁŃÓŚŹŻ0-9]{2,}\b\s+', content))
            sep_matches = re.findall(r'\s+\S{1,15}\s*[-–—−‐:=]\s+', " " + content)
            if (starts_with_sep or starts_with_upper) and len(sep_matches) >= 3:
                is_acronym_block = True
        
        # Wykrywanie blokow z akronimami, jeśli blok ma więcej niż trzy linijki
        elif total_lines > 3:
            acronym_lines = 0
            for data in paragraph_buffer:
                text = data['content'].strip()
                if is_acronym(text) == 1:
                    acronym_lines += 1
                    
            # Sprawdzenie, czy ilość linijek zaczynających się jak skróty jest większa niż threshhold 60%:
            if (acronym_lines / total_lines) >= 0.6: 
                is_acronym_block = True

        combined_content = ""
        combined_words = []
        current_offset = 0

        # Pętla zapisująca zawartość bufora
        for i, data in enumerate(paragraph_buffer):
            content = data['content']

            separator = ""
            if is_acronym_block and i > 0:
                separator = "\n"
            elif i > 0 and not combined_content.rstrip().endswith('-'):
                separator = " "

            for word in data['words']:
                shift = current_offset + len(separator)
                combined_words.append(WordInfo(
                    word_index=len(combined_words),
                    text=word.text,
                    start_char=word.start_char + shift,
                    end_char=word.end_char + shift,
                    font=word.font,
                    size=word.size,
                    bold=word.bold,
                    italic=word.italic,
                    bbox=word.bbox,
                    page_number=word.page_number,
                    line=word.line
                ))

            combined_content += separator + content
            current_offset = len(combined_content)

            # Detekcja wdów (maksymalnie 2 samotne słowa na końcu akapitu)
            is_widow = 0  

            if combined_words and len(combined_words) >= 2:
                last_word = combined_words[-1]
                second_to_last_word = combined_words[-2]    
                if last_word.line != second_to_last_word.line:
                    is_widow = 1
                elif len(combined_words) >= 3:
                    third_to_last_word = combined_words[-3]
                    if second_to_last_word.line != third_to_last_word.line:
                        is_widow = 2

            # Detekcja bękartów
            if combined_words:
                first_page = combined_words[0].page_number
                first_line = combined_words[0].line
                page_lines_buf = 1  
                has_page_break = False  
                words_line_buf = 1
            
                for word in combined_words:
                    if word.page_number != first_page:
                        first_page = word.page_number
                        first_line = word.line
                        page_lines_buf = 1  
                        has_page_break = True  
                        words_line_buf = 1           
                    elif word.line != first_line:
                        first_line = word.line
                        page_lines_buf += 1
                        words_line_buf = 1
                    else:
                        words_line_buf += 1
            
                if has_page_break and page_lines_buf <= 2:
                    is_bekart = words_line_buf
                else:
                    is_bekart = 0

            # Detekcja szewców
            is_szewc = 0
            if combined_words:
                first_page = combined_words[0].page_number
                first_line = combined_words[0].line
                page_lines_buf = 1  
                has_page_break = False  
                words_first_line_buf = 1 
                
                for word in combined_words[1:]:
                    if word.page_number != first_page:
                        has_page_break = True
                        break 
                        
                    elif word.line != first_line:
                        first_line = word.line
                        page_lines_buf += 1
                        
                    elif page_lines_buf == 1:
                        words_first_line_buf += 1

                if has_page_break and page_lines_buf == 1:
                    is_szewc = words_first_line_buf


        block_type = "acronyms" if is_acronym_block else "paragraph"

        if block_type == "paragraph":
            if PDFMapper.is_header(combined_words):
                block_type = "heading"
            elif PDFMapper.is_keywords(combined_words):
                block_type = "keywords"

        # Przypisanie wdowy tylko do bloku typu paragraf
        if block_type == "paragraph" and is_widow != 0:
            is_widow = is_widow
        else:
            is_widow = 0

        # Przypisanie bękarta tylko do bloku typu paragraf
        if block_type == "paragraph" and is_bekart != 0:
            is_bekart = is_bekart
        else:
            is_bekart = 0

        # Przypisanie szewca tylko do bloku typu paragraf
        if block_type == "paragraph" and is_szewc != 0:
            is_szewc = is_szewc
        else:
            is_szewc = 0

        logical_blocks.append(ParagraphBlock(
            block_id=paragraph_buffer[0]['block_id'],
            content=combined_content,
            words=combined_words,
            type=block_type,
            is_widow=is_widow,
            is_bekart=is_bekart,
            is_szewc=is_szewc,
            debug_empty=debug_why_empty
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

        curr_line = 0
        last_y1 = None

        for page in old_doc.pages:
            top_thresh = 50
            bottom_thresh = page.height - 75

            page_table_descs = {t.description for t in page.tables if t.description}
            page_img_descs = {img.description for img in page.images if img.description}

            table_bboxes = [t.bbox for t in page.tables]

            margins = calculate_margins(
                [{"bbox": b.bbox} for b in page.text_blocks], 
                page.width, 
                page.height
            )
            x0_margin = margins["left"]            
            margin_indent_thresh = 20
            


            for block in page.text_blocks:
                #if PDFMapper.is_inside_table(block.bbox, table_bboxes):
                #    continue
                full_text = ""
                words_info = []
                word_counter = 0

                temp_text = "".join(s.text for l in block.lines for s in l.spans).strip().lower()
                
                x0, y0, x1, y1 = block.bbox

                # Filtr kontynuacji listy
                is_valid_list_cont = False
                if list_buffer:
                    last_item = list_buffer[-1]
                    if PDFMapper.is_continuation(last_item['bbox'], list(block.bbox)):
                        is_valid_list_cont = True
                        # Filtr wertykalny
                        if last_y1 is not None and (y0 - last_y1) > 12: 
                            is_valid_list_cont = False
                        # Filtr wcięcia
                        text_x0 = last_item['bbox'][0]
                        if 'words' in last_item and len(last_item['words']) > 0:
                            for w in last_item['words']:
                                if w.bbox[0] > last_item['bbox'][0] + 3:
                                    text_x0 = w.bbox[0]
                                    break
                                    
                        if x0 < text_x0 - 5:
                            is_valid_list_cont = False

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
                    line_bbox = [line.spans[0].bbox[0], line.bbox[1], line.spans[-1].bbox[2], line.bbox[3]] if line.spans else line.bbox
                    if PDFMapper.is_inside_table(line_bbox, table_bboxes):
                        continue
                    tmp_line_text = "".join(s.text for s in line.spans).strip()
                    line_type, _ = classify_block_content(tmp_line_text)
                    
                    if line_type == "list" and full_text.strip():
                        prev_type, prev_marker = classify_block_content(full_text)
                        
                        if prev_type == "paragraph":
                            paragraph_buffer.append({
                                'content': full_text.strip(),
                                'words': words_info.copy(),
                                'block_id':block.block_id
                            })
                            PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer, "odcięcie wstępu od listy")
                            full_text = ""
                            words_info = []
                            curr_line = 0
                            
                        elif prev_type == "list":
                            cleaned_text = strip_list_marker(full_text, prev_marker)
                            list_buffer.append({
                                'item': ListItem(
                                    item_id=block.block_id, 
                                    marker_type=prev_marker, 
                                    text=cleaned_text, 
                                    bbox=list(block.bbox),
                                    words=words_info.copy()
                                ),
                                'words': words_info.copy(),
                                'block_id': block.block_id,
                                'bbox': list(block.bbox),
                                'original_text': full_text
                            })
                            full_text = ""
                            words_info = []

                    # Lewy koordynat x linii (do sprawdzenia, czy nowy akapit)
                    line_x0 = block.bbox[0]
                    if line.spans:
                        first_valid_span = next((s for s in line.spans if s.text.strip()), None)
                        if first_valid_span:
                            line_x0 = first_valid_span.bbox[0]
                        else:
                            line_x0 = line.spans[0].bbox[0]
                    
                    line_x1 = line.spans[-1].bbox[2] if line.spans else block.bbox[2]

                    
                    # Sprawdzanie, czy nowy akapit jeśli za duża różnica w pionie między linijkami
                    current_y0 = line.spans[0].bbox[1] if line.spans else line.bbox[1]
                    current_y1 = line.spans[-1].bbox[3] if line.spans else line.bbox[3]

                    # Detekcja nowego akapitu
                    is_new_paragraph = False
                    debug_reason = ""

                    # Wertykalna przerwa
                    if last_y1 is not None:
                        if current_y0 < last_y1 - 10:
                            last_y1 = None
                        else:
                            vertical_gap = current_y0 - last_y1
                            line_height = current_y1 - current_y0
                            if vertical_gap > line_height * 1.5:
                                is_new_paragraph = True
                                debug_reason = "zbyt duża wertykalna przerwa"
                    
                    last_y1 = current_y1

                    # Wcięcie akapitowe 
                    if not is_new_paragraph:
                        if not full_text.strip() and (line_x0 > x0_margin + margin_indent_thresh):
                            is_new_paragraph = True
                            debug_reason = "wcięcie na początku bloku/strony"

                    is_list_continuation = bool(list_buffer and PDFMapper.is_continuation(list_buffer[-1]['bbox'], list(block.bbox)))
                    if is_valid_list_cont:
                        is_new_paragraph = False

                    # Egzekucja podziału
                    if is_new_paragraph:
                        if full_text.strip():
                            paragraph_buffer.append({
                                'content': full_text.strip(),
                                'words': words_info.copy(),
                                'block_id': block.block_id
                            })
                            full_text = ""
                            words_info = []
                        
                        # Opróżnienie akaitów w razie wykrycia nowego akapitu 
                        if list_buffer:
                            PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                        if paragraph_buffer:
                            PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer, debug_reason)
                            curr_line = 0

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
                            page_number=page.number,
                            line = curr_line
                        ))
                        
                        full_text += word_text
                        prev_span_x1 = span.bbox[2]
                        word_counter += 1
                    curr_line += 1
                    
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
                #if normalized_text in clean_table_descs:
                #    current_type = "table_description"
                #elif normalized_text in clean_img_descs:
                #    current_type = "img_decription"

                if current_type:
                    PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer, "wykryto blok opisu tabeli/zdjęcia")
                    curr_line = 0
                    PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                    
                    new_doc.logical_blocks.append(ParagraphBlock(
                        block_id=block.block_id,
                        content=full_text,
                        words=words_info,
                        type=current_type
                    ))
                    continue
                
                if PDFMapper.is_header(words_info):
                    PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer, "wykryto nagłówek")
                    curr_line = 0
                    PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                    
                    new_doc.logical_blocks.append(ParagraphBlock(
                        block_id=block.block_id,
                        content=full_text,
                        words=words_info,
                        type="heading", 
                        debug_empty="wykryto nagłówek"
                    ))
                    continue

                block_type, marker_type = classify_block_content(full_text)

                if block_type == "list":
                    PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer, "wykryto listę")
                    curr_line = 0
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
                elif is_valid_list_cont: 
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
                    last_item_data['bbox'] = last_item_data['item'].bbox
                else:
                    PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
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
                    caption="",
                    table_data=table.data,
                    format={"num_rows": table.row_count, "num_columns": table.col_count}
                )
                new_doc.floating_elements.visual_elements.append(ve)

        # Opróżnianie buforów dopiero po przetworzeniu wszystkich stron, by uniknąć urywania akapitów
        PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
        PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer, "finalne opróżnienie")
        
        # Łączenie nagłówków
        i = 0
        logical_blocks = new_doc.logical_blocks
        while i < len(logical_blocks) - 1:
            curr = logical_blocks[i]
            nxt = logical_blocks[i+1]

            if (getattr(curr, "type", None) == "heading" and 
                getattr(nxt, "type", None) == "heading"):
                
                separator = " "
                old_len = len(curr.content) + len(separator)
                curr.content += separator + nxt.content
                
                for word in nxt.words:
                    word.start_char += old_len
                    word.end_char += old_len
                    word.word_index += len(curr.words)
                    curr.words.append(word)
                
                logical_blocks.pop(i + 1)
                continue 
            
            i += 1

        # Finalne przypisanie opisów do tabel i obrazów (TODO: poprawić)
        for page in old_doc.pages:
            for table in page.tables:
                desc_text, found_side = find_table_description(list(table.bbox), new_doc.logical_blocks, priority_side="above")
                
                final_caption = desc_text if desc_text else table.description

                ve = VisualElement(
                    element_id=id(table),
                    type="table",
                    page_number=page.number,
                    bbox=list(table.bbox),
                    caption={"text": final_caption},
                    table_data=table.data,
                    format={"num_rows": table.row_count, "num_columns": table.col_count}
                )
                new_doc.floating_elements.visual_elements.append(ve)
                
                if final_caption:
                    for lb in new_doc.logical_blocks:
                        if hasattr(lb, 'content') and lb.content.strip() == final_caption:
                            lb.type = "table_description"
                            break

            for img in page.images:
                 desc_text, found_side = find_image_description(list(img.bbox), new_doc.logical_blocks, priority_side="below")
                 if desc_text:
                     for lb in new_doc.logical_blocks:
                         if hasattr(lb, 'content') and lb.content.strip() == desc_text:
                             lb.type = "image_description"
                             break

        return new_doc

MULTISPACE_RE = re.compile(r"\s+")


def clean_ws(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")
    return MULTISPACE_RE.sub(" ", text).strip()


def get_plain_text(pdf_path):
    raw_doc = extractPDF(str(pdf_path))
    mapped_doc = PDFMapper.map_to_schema(raw_doc)

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