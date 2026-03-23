from schema import (
    FinalDocument, ParagraphBlock, ListBlock, ListItem, 
    WordInfo, VisualElement, FloatingElements, ReferenceSections,
    classify_block_content, strip_list_marker
)
from extraction_json import DocumentData, extractPDF
from pathlib import Path
from schema import PageArtifact 
from typing import List, Dict, Any, Union, Optional

class PDFMapper:

    # Heurystyczne sprawdzenie czy coś jest nagłówkiem
    @staticmethod
    def is_header(words: list[WordInfo]) -> bool:
        if not words: return False
        
        is_bold = all(w.bold for w in words)
        avg_size = sum(w.size for w in words) / len(words)
        
        return (is_bold and len(words) < 15) or avg_size > 12.5
    
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

        if len(list_buffer) > 1:
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
            logical_blocks.append(ParagraphBlock(
                block_id=data['block_id'],
                content=data['item'].text,
                words=data['words'] 
            ))
        
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
        
            for block in page.text_blocks:
                full_text = ""
                words_info = []
                word_counter = 0
                current_pos = 0

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
                    for span in line.spans:
                        word_text = span.text
                        start_char = current_pos
                        end_char = start_char + len(word_text)
                        
                        w_info = WordInfo(
                            word_index=word_counter,
                            text=word_text,
                            start_char=start_char,
                            end_char=end_char,
                            font=span.font,
                            size=span.size,
                            bold=span.bold,
                            italic=span.italic,
                            bbox=list(span.bbox),
                            page_number=page.number
                        )
                        words_info.append(w_info)
                        
                        # Budujemy tekst i aktualizujemy pozycję dla następnego słowa
                        full_text += word_text + " "
                        current_pos = end_char + 1  # +1, bo dodaliśmy spację
                        word_counter += 1
                
                full_text = full_text.strip()
                if not full_text: continue
                if len(full_text) < 2: 
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

                if block_type == "list":
                    PDFMapper.empty_paragraph_buffer(new_doc.logical_blocks, paragraph_buffer) #lista przerywa akapit
                    cleaned_text = strip_list_marker(full_text, marker_type)
                    list_buffer.append({
                        'item': ListItem(item_id=block.block_id, marker_type=marker_type, text=cleaned_text, bbox=list(block.bbox)),
                        'words': words_info,
                        'block_id': block.block_id,
                        'bbox': list(block.bbox),
                        'original_text': full_text
                    })
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

if __name__ == "__main__":
    pdf_path = Path("src/theses/doju1.pdf")
    
    if pdf_path.exists():
        raw_data = extractPDF(str(pdf_path))
        final_doc = PDFMapper.map_to_schema(raw_data)
        final_doc.to_json("src/redaction/output.json")
        print("JSON wygenerowany")
    else:
        print(f"Błąd: Nie znaleziono pliku {pdf_path}")

