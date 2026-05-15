'''
Struktura (wraz z wieloma metodami) do mapowania surowych danych 
z ekstrakcji PDF na bardziej ustrukturyzowany format, który jest 
przyjazny dla dalszej analizy lingwistycznej i NLP.
'''
import re
import statistics
import fitz  # PyMuPDF
from typing import Dict

from analysis.extraction.schema import (
    FinalDocument, ParagraphBlock, ListBlock, ListItem, 
    WordInfo, VisualElement, FloatingElements, ReferenceSections,
    classify_block_content, strip_list_marker
)

#from src.analysis.extraction.schema import (
#    FinalDocument, ParagraphBlock, ListBlock, ListItem, 
#    WordInfo, VisualElement, FloatingElements, ReferenceSections,
#    classify_block_content, strip_list_marker
#)
from analysis.extraction.extraction_json import DocumentData, extractPDF, calculate_margins
from analysis.extraction.schema import PageArtifact, is_acronym, find_table_description, find_image_description, is_widow_func, is_bekart_func, is_szewc_func 


#from src.analysis.extraction.extraction_json import DocumentData, extractPDF, calculate_margins
#from src.analysis.extraction.schema import PageArtifact, is_acronym, find_table_description, find_image_description, is_widow_func, is_bekart_func, is_szewc_func 
class PDFMapper:
    
    # Stałe
    TOP_MARGIN_THRESH = 50
    BOTTOM_MARGIN_OFFSET = 75
    MARGIN_INDENT_THRESH = 20
    MIN_VERTICAL_GAP = 11.5
    ACRONYM_THRESH = 0.6
    LIST_CONT_MAX_X_DIFF = 10
    TABLE_INTERSECT_THRESH = 0.8
    MIN_VERTICAL_GAP_LIST = 50

    def __init__(self):
        # Stan wewnętrzny
        self.logical_blocks = []
        self.paragraph_buffer = []
        self.list_buffer = []
        self.curr_line = 0
        self.last_y1 = None

    # Metody statyczne (Pomocnicze, bez stanu)
    @staticmethod
    def is_continuation(last_item_bbox: list, current_block_bbox: list) -> bool:
        last_x0 = last_item_bbox[0]
        curr_x0 = current_block_bbox[0]
        return abs(last_x0 - curr_x0) < PDFMapper.LIST_CONT_MAX_X_DIFF or curr_x0 > last_x0
    
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

    @staticmethod
    def is_math(words: list[WordInfo]) -> bool:
        if not words: return False

        math_font_count = sum(1 for w in words if any(mf in w.font.lower() for mf in ['math', 'cmmi', 'cmr', 'cmsy', 'symbol']))
        if len(words) > 0 and (math_font_count / len(words)) > 0.4:
            return True
        
        full_text = "".join(w.text for w in words).replace(" ", "")
        if not full_text: return False

        math_chars_pattern = r'[0-9=\+\-\*/<>\∑\∫\∏\√\∞\≈\≠\≡\≤\≥\{\}\(\)\[\]\|\α-\ω\Α-\Ω]'
        math_chars_count = len(re.findall(math_chars_pattern, full_text))
        
        single_letter_count = sum(1 for w in words if len(w.text) == 1 and w.text.isalpha())

        ratio = (math_chars_count + single_letter_count) / len(full_text)
        
        return ratio > 0.35 
    
    @staticmethod
    def is_inside_table(block_bbox: list, table_bboxes: list) -> bool:
        bx0, by0, bx1, by1 = block_bbox
        block_area = (bx1 - bx0) * (by1 - by0)
        if block_area <= 0: return False

        for tx0, ty0, tx1, ty1 in table_bboxes:
            ix0 = max(bx0, tx0 - 5)
            iy0 = max(by0, ty0 - 5)
            ix1 = min(bx1, tx1 + 5)
            iy1 = min(by1, ty1 + 5)
            if ix0 < ix1 and iy0 < iy1:
                intersect_area = (ix1 - ix0) * (iy1 - iy0)
                if intersect_area / block_area > PDFMapper.TABLE_INTERSECT_THRESH: 
                    return True
        return False

    # Zarządzanie buforami (Wymagają stanu) 
    def _empty_paragraph_buffer(self, debug_why_empty=""):
        if not self.paragraph_buffer:
            return
        
        is_acronym_block = False
        total_lines = len(self.paragraph_buffer)
        is_widow = 0
        is_bekart = 0
        is_szewc = 0

        # Wykrywanie bloków z akronimami (przypadki, gdzie całość zlepiona w jedną linijkę)
        if total_lines == 1:
            content = self.paragraph_buffer[0]['content'].strip()
            starts_with_sep = bool(re.match(r'^\S{1,15}\s*[-–—−‐:=]\s+', content))
            starts_with_upper = bool(re.match(r'^[A-ZĄĆĘŁŃÓŚŹŻ0-9]{2,}\b\s+', content))
            sep_matches = re.findall(r'\s+\S{1,15}\s*[-–—−‐:=]\s+', " " + content)
            if (starts_with_sep or starts_with_upper) and len(sep_matches) >= 3:
                is_acronym_block = True
        
        # Wykrywanie bloków z akronimami (więcej niż trzy linijki)
        elif total_lines > 3:
            acronym_lines = 0
            for data in self.paragraph_buffer:
                text = data['content'].strip()
                if is_acronym(text) == 1:
                    acronym_lines += 1
            if (acronym_lines / total_lines) >= self.ACRONYM_THRESH: 
                is_acronym_block = True

        combined_content = ""
        combined_words = []
        current_offset = 0

        # Pętla zapisująca zawartość bufora
        for i, data in enumerate(self.paragraph_buffer):
            content = data['content']
            separator = ""
            removed_hyphen = False

            if is_acronym_block and i > 0:
                separator = "\n"
            elif i > 0:
                if combined_content.rstrip().endswith('-'):
                    separator = ""
                    removed_hyphen = True
                else:
                    separator = " "

            if removed_hyphen:
                combined_content = combined_content.rstrip()[:-1]
                current_offset = len(combined_content)

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

        block_type = "acronyms" if is_acronym_block else "paragraph"

        if block_type == "paragraph":
            if PDFMapper.is_header(combined_words):
                block_type = "heading"
            elif PDFMapper.is_keywords(combined_words):
                block_type = "keywords"
            elif PDFMapper.is_math(combined_words):  
                block_type = "math"

        # Przypisanie wdowy, szewca i bękarta tylko do bloku typu paragraf
        if block_type == "paragraph":
            is_widow = is_widow_func(combined_words) if is_widow_func(combined_words) != 0 else 0
            is_bekart = is_bekart_func(combined_words) if is_bekart_func(combined_words) != 0 else 0
            is_szewc = is_szewc_func(combined_words) if is_szewc_func(combined_words) != 0 else 0

        self.logical_blocks.append(ParagraphBlock(
            block_id=self.paragraph_buffer[0]['block_id'],
            content=combined_content,
            words=combined_words,
            type=block_type,
            is_widow=is_widow,
            is_bekart=is_bekart,
            is_szewc=is_szewc,
            debug_empty=debug_why_empty
        ))
        self.paragraph_buffer.clear()

    def _empty_list_buffer(self): 
        if not self.list_buffer:
            return
        
        items = [data['item'] for data in self.list_buffer]
        all_words = []
        for item in items:
            all_words.extend(item.words)
            
        combined_content = "\n".join(item.text for item in items)

        if len(items) > 1:
            first_item_data = self.list_buffer[0]

            is_bibiography = True if getattr(self, "in_bibliography_section", False) else False
            data = self.list_buffer[0]
            item = data['item']

            if item.marker_type == "listing":
                list_type = "code_snippet"
            else: 
                list_type = "list"

            new_list_block = ListBlock(
                block_id=f"list_{first_item_data['block_id']}",
                content=combined_content,
                is_bibliography=is_bibiography,
                words=all_words,
                items=items,
                bbox=first_item_data['bbox'], 
                type=list_type
            )

            all_bboxes = [item.bbox for item in items]
            new_list_block.bbox = [
                min(b[0] for b in all_bboxes), min(b[1] for b in all_bboxes),
                max(b[2] for b in all_bboxes), max(b[3] for b in all_bboxes)
            ]
            self.logical_blocks.append(new_list_block)
        else:
            data = self.list_buffer[0]
            item = data['item']
            #if item.marker_type == "number_with_dot" or item.marker_type == "bullet":
            self.logical_blocks.append(ParagraphBlock(
                block_id=data['block_id'], content=item.text, words=item.words 
            ))
            #else:
            #    self.logical_blocks.append(ListBlock(
            #        block_id=f"list_{data['block_id']}", content=item.text, words=item.words, items=[item], bbox=item.bbox
            #    ))
        self.list_buffer.clear()

    # Logika podziału i (wielokrotnych) spacji
    def _detect_paragraph_break(self, current_y0, current_y1, line_x0, x0_margin, full_text, is_valid_list_cont):
        is_new_paragraph = False
        debug_reason = ""

        # Wertykalna przerwa
        if self.last_y1 is not None:
            if current_y0 < self.last_y1 - 10:
                self.last_y1 = None
            else:
                vertical_gap = current_y0 - self.last_y1
                line_height = current_y1 - current_y0
                if vertical_gap > line_height * 1.5:
                    is_new_paragraph = True
                    debug_reason = "zbyt duża wertykalna przerwa"
        
        self.last_y1 = current_y1

        # Wcięcie akapitowe 
        if not is_new_paragraph:
            if not full_text.strip() and (line_x0 > x0_margin + self.MARGIN_INDENT_THRESH):
                is_new_paragraph = True
                debug_reason = "wcięcie na początku bloku/strony"

        if is_valid_list_cont:
            is_new_paragraph = False

        return is_new_paragraph, debug_reason

    def _extract_words_with_spacing(self, line, full_text, words_info, page_num, word_counter, line_x1):
        line_gaps = []
        for i in range(len(line.spans) - 1):
            g = line.spans[i+1].bbox[0] - line.spans[i].bbox[2]
            if g > 0: line_gaps.append(g)
        
        m_gap = statistics.median(line_gaps) if line_gaps else 3.0
        prev_span_x1 = None

        for span in line.spans:
            word_text = span.text.replace('\u200b', '').strip()
            if not word_text: continue
            
            if prev_span_x1 is not None:
                current_gap = span.bbox[0] - prev_span_x1
                
                if not (full_text.rstrip().endswith('-') and abs(line_x1 - span.bbox[2]) < 50):
                    full_text += " "
                
                after_punct = full_text.strip().endswith(('.', '!', '?', ':', ';'))
                
                if current_gap > 1.2 * m_gap and not after_punct: full_text += " "
                if current_gap > 1.5 * m_gap and after_punct: full_text += " "

            # Logika rozdzielania słów
            sub_words = word_text.split()
            
            span_x0, span_y0, span_x1, span_y1 = span.bbox
            span_width = span_x1 - span_x0
            total_chars = len(word_text)
            
            current_sub_x0 = span_x0

            for i, sub_w in enumerate(sub_words):
                if i > 0:
                    full_text += " " 
                
                start_char = len(full_text)
                
                sub_w_width = (len(sub_w) / total_chars) * span_width if total_chars > 0 else 0
                sub_x1 = current_sub_x0 + sub_w_width
                approx_bbox = [current_sub_x0, span_y0, sub_x1, span_y1]

                words_info.append(WordInfo(
                    word_index=word_counter, 
                    text=sub_w, 
                    start_char=start_char, 
                    end_char=start_char + len(sub_w),
                    font=span.font, 
                    size=span.size, 
                    bold=span.bold, 
                    italic=span.italic, 
                    bbox=approx_bbox,
                    page_number=page_num, 
                    line=self.curr_line
                ))
                
                full_text += sub_w
                word_counter += 1
                
                space_width = (1 / total_chars) * span_width if total_chars > 0 else 0
                current_sub_x0 = sub_x1 + space_width

            prev_span_x1 = span.bbox[2]

        self.curr_line += 1
        if not full_text.endswith(" ") and not full_text.rstrip().endswith("-"):
            full_text += " "

        return full_text, words_info, word_counter

    # Główna metoda mapowania
    def map_to_schema(self, old_doc: DocumentData) -> FinalDocument:
        # 1. Reset
        self.__init__()
        
        new_doc = FinalDocument(
            metadata=old_doc.metadata,
            floating_elements=FloatingElements(),
            reference_sections=ReferenceSections()
        )
        self.logical_blocks = new_doc.logical_blocks

        # 2. Przetwarzanie stron
        for page in old_doc.pages:
            self._process_page(page, new_doc)

        # 3. Opróżnianie pozostałości z buforów
        self._empty_list_buffer()
        self._empty_paragraph_buffer("finalne opróżnienie")
        
        # 4. Post-processing (Łączenie nagłówków i podpisy)
        self._merge_adjacent_headings()
        self._assign_captions_to_visuals(old_doc.pages, new_doc)
        self._tag_special_lists(old_doc)

        # 5. Wyciąganie akronimów
        self._extract_acronyms_to_schema(new_doc)

        return new_doc

    def _process_page(self, page, new_doc):
        bottom_thresh = page.height - self.BOTTOM_MARGIN_OFFSET
        table_bboxes = [t.bbox for t in page.tables]
        

        margins = calculate_margins([{"bbox": b.bbox} for b in page.text_blocks], page.width, page.height)
        x0_margin = margins["left"]            

        for block in page.text_blocks:
            current_marker = self.list_buffer[-1]['item'].marker_type if self.list_buffer else None
            full_text = ""
            words_info = []
            word_counter = 0

            temp_text = "".join(s.text for l in block.lines for s in l.spans).strip().lower()
            x0, y0, x1, y1 = block.bbox

            # Filtr kontynuacji listy
            is_valid_list_cont = False
            if self.list_buffer:
                raw_block_text = "".join(s.text for l in block.lines for s in l.spans).strip()
                current_block_type, _ = classify_block_content(raw_block_text, current_marker)
                allowed_gap = self.MIN_VERTICAL_GAP_LIST if current_block_type == "list" else self.MIN_VERTICAL_GAP
                last_item = self.list_buffer[-1]
                if self.is_continuation(last_item['bbox'], list(block.bbox)):
                    is_valid_list_cont = True
                    if self.last_y1 is not None and (y0 - self.last_y1) > allowed_gap: 
                        is_valid_list_cont = False
                    
                    text_x0 = last_item['bbox'][0]
                    if 'words' in last_item and len(last_item['words']) > 0:
                        for w in last_item['words']:
                            if w.bbox[0] > last_item['bbox'][0] + 3:
                                text_x0 = w.bbox[0]
                                break
                    if x0 < text_x0 - 5:
                        is_valid_list_cont = False

            # Artefakty (stopki / nagłówki)
            if y1 < self.TOP_MARGIN_THRESH or y0 > bottom_thresh:
                new_artifact = PageArtifact(
                    artifact_id=block.block_id, type="nr strony (tymczasowo uproszczone)", 
                    page_number=page.number, text=temp_text, bbox=list(block.bbox)
                )
                new_doc.floating_elements.page_artifacts.append(new_artifact)
                continue

            for line in block.lines:
                line_bbox = [line.spans[0].bbox[0], line.bbox[1], line.spans[-1].bbox[2], line.bbox[3]] if line.spans else line.bbox
                if self.is_inside_table(line_bbox, table_bboxes):
                    continue
                
                tmp_line_text = "".join(s.text for s in line.spans).strip()
                line_type, _ = classify_block_content(tmp_line_text, current_marker)
                
                if line_type == "list" and full_text.strip():
                    prev_type, prev_marker = classify_block_content(full_text, current_marker)
                    if prev_type == "paragraph":
                        self.paragraph_buffer.append({'content': full_text.strip(), 'words': words_info.copy(), 'block_id': block.block_id})
                        self._empty_paragraph_buffer("odcięcie wstępu od listy")
                        full_text, words_info, self.curr_line = "", [], 0
                    elif prev_type == "list":
                        cleaned_text = strip_list_marker(full_text, prev_marker)
                        self.list_buffer.append({
                            'item': ListItem(item_id=block.block_id, marker_type=prev_marker, text=cleaned_text, bbox=list(block.bbox), words=words_info.copy()),
                            'words': words_info.copy(), 'block_id': block.block_id, 'bbox': list(block.bbox), 'original_text': full_text
                        })
                        full_text, words_info = "", []

                line_x0 = block.bbox[0]
                if line.spans:
                    first_valid_span = next((s for s in line.spans if s.text.strip()), None)
                    line_x0 = first_valid_span.bbox[0] if first_valid_span else line.spans[0].bbox[0]
                
                line_x1 = line.spans[-1].bbox[2] if line.spans else block.bbox[2]
                current_y0 = line.spans[0].bbox[1] if line.spans else line.bbox[1]
                current_y1 = line.spans[-1].bbox[3] if line.spans else line.bbox[3]

                # Detekcja nowego akapitu
                is_new_paragraph, debug_reason = self._detect_paragraph_break(current_y0, current_y1, line_x0, x0_margin, full_text, is_valid_list_cont)

                

                if is_new_paragraph:
                    if full_text.strip():
                        prev_type, prev_marker = classify_block_content(full_text, current_marker)
            
                        if prev_type == "list":
                            cleaned_text = strip_list_marker(full_text, prev_marker)
                            self.list_buffer.append({
                                'item': ListItem(item_id=block.block_id, marker_type=prev_marker, text=cleaned_text, bbox=list(block.bbox), words=words_info.copy()),
                                'words': words_info.copy(), 'block_id': block.block_id, 'bbox': list(block.bbox), 'original_text': full_text
                            })
                        else:
                            if self.list_buffer:
                                self._empty_list_buffer()
                            self.paragraph_buffer.append({'content': full_text.strip(), 'words': words_info.copy(), 'block_id': block.block_id})
                
                        full_text, words_info = "", []
        
                    if self.paragraph_buffer:
                        self._empty_paragraph_buffer(debug_reason)
                        self.curr_line = 0

                # Ekstrakcja słów do linijki
                full_text, words_info, word_counter = self._extract_words_with_spacing(line, full_text, words_info, page.number, word_counter, line_x1)
            
            full_text = full_text.strip()
            if not full_text or len(full_text) < 2: continue

            if self.is_header(words_info):
                self._empty_paragraph_buffer("wykryto nagłówek")
                self.curr_line = 0
                self._empty_list_buffer()

                if full_text.upper().startswith(("BIBLIOGRAFIA", "LITERATURA", "REFERENCES", "WYKAZ LITERATURY")):
                    self.in_bibliography_section = True
                else: 
                    self.in_bibliography_section = False

                self.logical_blocks.append(ParagraphBlock(block_id=block.block_id, content=full_text, words=words_info, type="heading", debug_empty="wykryto nagłówek"))
                continue

            block_type, marker_type = classify_block_content(full_text, current_marker)

            if block_type == "list":
                self._empty_paragraph_buffer("wykryto listę")
                self.curr_line = 0
                cleaned_text = strip_list_marker(full_text, marker_type)
                self.list_buffer.append({
                    'item': ListItem(item_id=block.block_id, marker_type=marker_type, text=cleaned_text, bbox=list(block.bbox), words=words_info),
                    'words': words_info, 'block_id': block.block_id, 'bbox': list(block.bbox), 'original_text': full_text
                })
            elif is_valid_list_cont: 
                last_item_data = self.list_buffer[-1]
                connector = "" if last_item_data['item'].text.rstrip().endswith('-') else " "
                last_item_data['item'].text += connector + full_text
                last_item_data['item'].words.extend(words_info)
                b = list(block.bbox)
                last_item_data['item'].bbox = [
                    min(last_item_data['item'].bbox[0], b[0]), min(last_item_data['item'].bbox[1], b[1]),
                    max(last_item_data['item'].bbox[2], b[2]), max(last_item_data['item'].bbox[3], b[3])
                ]
                last_item_data['bbox'] = last_item_data['item'].bbox
            else:
                self._empty_list_buffer()
                self.paragraph_buffer.append({'content': full_text, 'words': words_info, 'block_id': block.block_id})

        for table in page.tables:
            ve = VisualElement(
                element_id=id(table), type="table", page_number=page.number, bbox=list(table.bbox),
                caption="", table_data=table.data, format={"num_rows": table.row_count, "num_columns": table.col_count}
            )
            new_doc.floating_elements.visual_elements.append(ve)

    def _merge_adjacent_headings(self):
        i = 0
        while i < len(self.logical_blocks) - 1:
            curr = self.logical_blocks[i]
            nxt = self.logical_blocks[i+1]

            if getattr(curr, "type", None) == "heading" and getattr(nxt, "type", None) == "heading":
                separator = " "
                old_len = len(curr.content) + len(separator)
                curr.content += separator + nxt.content
                
                for word in nxt.words:
                    word.start_char += old_len
                    word.end_char += old_len
                    word.word_index += len(curr.words)
                    curr.words.append(word)
                
                self.logical_blocks.pop(i + 1)
                continue 
            i += 1

    def _assign_captions_to_visuals(self, pages, new_doc):
        for page in pages:
            for table in page.tables:
                desc_text, _ = find_table_description(list(table.bbox), self.logical_blocks, priority_side="above")
                final_caption = desc_text if desc_text else table.description

                ve = next((v for v in new_doc.floating_elements.visual_elements if v.element_id == id(table)), None)
                if ve: ve.caption = {"text": final_caption}
                
                if final_caption:
                    for lb in self.logical_blocks:
                        if hasattr(lb, 'content') and lb.content.strip() == final_caption:
                            lb.type = "table_description"
                            break

            for img in page.images:
                desc_text, _ = find_image_description(list(img.bbox), self.logical_blocks, priority_side="below")
                if desc_text:
                    for lb in self.logical_blocks:
                        if hasattr(lb, 'content') and lb.content.strip() == desc_text:
                            lb.type = "image_description"
                            break
    
    def _tag_special_lists(self, old_doc: DocumentData):
        """
        Post-processing: Zmienia typ bloków na 'toc', 'tot' lub 'tof' 
        jeśli ich bboxy pokrywają się z danymi z ekstraktora.
        """
        special_bboxes = {} 
        
        def add_entries(entries, tag):
            if not entries: return
            for entry in entries:
                if entry.src_page == -1: 
                    continue 
                if entry.src_page not in special_bboxes:
                    special_bboxes[entry.src_page] = {'toc': [], 'tot': [], 'tof': []}
                special_bboxes[entry.src_page][tag].append(entry.bbox)

        add_entries(old_doc.toc.entries if old_doc.toc else [], 'toc')
        add_entries(old_doc.tot.entries if old_doc.tot else [], 'tot')
        add_entries(old_doc.tof.entries if old_doc.tof else [], 'tof') 

        if not special_bboxes:
            return 

        for block in self.logical_blocks:
            words = getattr(block, 'words', [])
            if not words:
                continue
            
            page_num = words[0].page_number
            if page_num not in special_bboxes:
                continue
            
            bx0 = min(w.bbox[0] for w in words)
            by0 = min(w.bbox[1] for w in words)
            bx1 = max(w.bbox[2] for w in words)
            by1 = max(w.bbox[3] for w in words)
            
            matched_tag = None
            for tag in ['toc', 'tot', 'tof']:
                for t_bbox in special_bboxes[page_num][tag]:
                    ix0 = max(bx0, t_bbox[0] - 5)
                    iy0 = max(by0, t_bbox[1] - 5)
                    ix1 = min(bx1, t_bbox[2] + 5)
                    iy1 = min(by1, t_bbox[3] + 5)
                    
                    if ix0 < ix1 and iy0 < iy1: #
                        matched_tag = tag
                        break
                if matched_tag:
                    break
            
            if matched_tag:
                block.type = matched_tag
    
    def _extract_acronyms_to_schema(self, new_doc):
        from schema import AcronymItem
        import re 
        
        # Wzorzec 1: Dla skrótów z myślnikami 
        PATTERN_DASH = re.compile(r'\b([A-ZĄĆĘŁŃÓŚŹŻ0-9]{2,15})\s*[-–—−]\s*(.*?)(?=\s*\b[A-ZĄĆĘŁŃÓŚŹŻ0-9]{2,15}\s*[-–—−]|$)')
        
        # Wzorzec 2: Dla skrótów ze spacją z poprzedniego PDFa 
        PATTERN_SPACE = re.compile(r'\b([A-ZĄĆĘŁŃÓŚŹŻ0-9]{2,15})\s+(.*?)(?=\s*\b[A-ZĄĆĘŁŃÓŚŹŻ0-9]{2,15}\s+[A-ZĄĆĘŁŃÓŚŹŻ]|$)')
        
        in_acronym_section = False
        
        for block in self.logical_blocks:
            
            if getattr(block, "type", None) == "heading":
                header_text = block.content.strip().upper()
                # Sprawdzenie nagłówka (dodano "ABBREVIATION" z Twojego PDF-a)
                if "ACRONYM" in header_text or "SKRÓT" in header_text or "ABBREVIATION" in header_text or "OZNACZEŃ" in header_text:
                    in_acronym_section = True
                else:
                    in_acronym_section = False
                continue 

            if in_acronym_section and getattr(block, "type", None) in ["acronyms", "paragraph", "math"]:
                lines = block.content.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    if re.search(r'\.{3,}', line):
                        continue
                    
                    # Automatyczne wykrywanie formatu: Czy ta linijka używa myślników jako separatora?
                    if re.search(r'(?:^|\s+)[A-Za-z0-9\-]{2,15}\s+[-–—]', line):
                        active_pattern = PATTERN_DASH
                    else:
                        active_pattern = PATTERN_SPACE

                    # Tniemy złączony tekst używając odpowiedniego wzorca
                    for match in active_pattern.finditer(line):
                        acronym = match.group(1).strip()
                        raw_definition = match.group(2).strip()
                        
                        def_match = re.match(r'^(.*?)(?:\.\s*([\d,\-\s\u2013\u2014]+))?$', raw_definition)
                        
                        if def_match:
                            definition = def_match.group(1).strip()
                            pages = def_match.group(2).strip() if def_match.group(2) else ""
                        else:
                            definition = raw_definition
                            pages = ""
                        
                        definition = re.sub(r'^[-–—−‐:=]\s*', '', definition)
                            
                        # Wydłużony limit, na wypadek wyjątkowo długich definicji
                        if len(definition) < 2 or len(definition) > 350:
                             continue

                        new_item = AcronymItem(
                            acronym=acronym,
                            definition=definition,
                            pages=pages,
                            bbox=[],  
                            words=[]  
                        )
                        new_doc.reference_sections.acronyms.append(new_item)

# Funkcje zewnętrzne

MULTISPACE_RE = re.compile(r"\s+")

def clean_ws(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\xa0", " ")
    return MULTISPACE_RE.sub(" ", text).strip()

def get_plain_text(pdf_path):
    raw_doc = extractPDF(str(pdf_path))
    
    mapper = PDFMapper()
    mapped_doc = mapper.map_to_schema(raw_doc)

    parts = []
    for block in mapped_doc.logical_blocks:
        block_type = getattr(block, "type", None)
        text = clean_ws(getattr(block, "content", "") or "")

        if not text:
            continue

        if block_type in {"list", "table_description", "img_decription", "math"}:
            continue

        parts.append(text)

    return clean_ws(" ".join(parts))

def get_acronyms_lut(doc) -> dict:
    return {item.acronym: item.definition for item in doc.reference_sections.acronyms}