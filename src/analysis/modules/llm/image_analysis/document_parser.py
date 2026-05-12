import fitz
import re

class DocumentParser:
    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        doc = fitz.open(self.file_path)
        paragraphs = []
        images = []

        caption_pattern = re.compile(r"(?i)rys(?:unek|\.)?\s*(\d+(?:\.\d+)?)")

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("blocks")
            
            for b in blocks:
                if b[6] == 0: 
                    paragraphs.append(b[4].replace("\n", " ").strip())

            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
            
                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                
                img_bottom = rects[0].y1 
                found_id = None
                
                candidate_blocks = [
                    b for b in blocks 
                    if b[6] == 0 and (img_bottom - 50) <= b[1] <= (img_bottom + 150)
                ]

                candidate_blocks.sort(key=lambda b: b[1])
                
                for b in candidate_blocks:
                    text = b[4].replace("\n", " ").strip()
                    match = caption_pattern.search(text)
                    if match:
                        found_id = match.group(1) 
                        break
                        
                if found_id:
                    images.append({
                        "id": found_id,
                        "bytes": image_bytes
                    })

        return paragraphs, images