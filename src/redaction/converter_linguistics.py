from schema import (
    FinalDocument, ParagraphBlock, ListBlock, ListItem, 
    WordInfo, VisualElement, FloatingElements, ReferenceSections,
    classify_block_content
)
from extraction_json import DocumentData, extractPDF
from pathlib import Path
from schema import PageArtifact 


class PDFMapper:

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

        for page in old_doc.pages:
            top_thresh = 50
            bottom_thresh = page.height - 50
        
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
                    for span in line.spans:
                        full_text += span.text + " "
                        words_info.append(WordInfo(
                            word_index=word_counter,
                            text=span.text,
                            font=span.font,
                            size=span.size,
                            bold=span.bold,
                            italic=span.italic,
                            bbox=list(span.bbox),
                            page_number=page.number
                        ))
                        word_counter += 1
                
                full_text = full_text.strip()
                if not full_text: continue

                block_type, marker_type = classify_block_content(full_text) # Klasyfikacja jako lista lup paragraf (początkowa, później sprawdzana ilość elementów)

                if block_type == "list":
                    list_buffer.append({
                        'item': ListItem(item_id=block.block_id, marker_type=marker_type, text=full_text, bbox=list(block.bbox)),
                        'words': words_info,
                        'block_id': block.block_id,
                        'bbox': list(block.bbox)
                    })
                else:
                    PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)
                    
                    new_doc.logical_blocks.append(ParagraphBlock(
                        block_id=block.block_id,
                        content=full_text,
                        words=words_info
                    ))

            PDFMapper.empty_list_buffer(new_doc.logical_blocks, list_buffer)

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
    pdf_path = Path("pdf_diploma_checker/src/theses/doju1.pdf")
    
    if pdf_path.exists():
        raw_data = extractPDF(str(pdf_path))
        final_doc = PDFMapper.map_to_schema(raw_data)
        final_doc.to_json("output.json")
        print("JSON wygenerowany")
    else:
        print(f"Błąd: Nie znaleziono pliku {pdf_path}")