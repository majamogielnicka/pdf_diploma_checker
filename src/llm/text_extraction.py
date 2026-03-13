import fitz
from dataclasses import dataclass, field

@dataclass
class ChapterBlock:
    id: int
    title: str
    content: str = ""

def get_content(file_path: str):
    doc = fitz.open(file_path)
    blocks = []
    
    current_title = ""
    current_text_parts = []
    block_id = 1
    font_size = 11 #Można zmienić w razie potrzeby

    for page in doc:
        page_dict = page.get_text("dict", sort=True)
        
        for b in page_dict["blocks"]:
            if "lines" not in b: continue
            
            for line in b["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text or text.isdigit():
                        continue
                    
                    size = span["size"]
                    is_bold = bool(span["flags"] & 16)
                    
                    #Warunek uznania za nagłówek: czcionka większ równa font_size, pogrubienie, długosć min. 4 znaki, wielkie litery
                    is_header = (size >= font_size and is_bold) and len(text) > 3 and text.isupper()

                    if is_header:
                        #zabezpieczenie przed przeniesieniami tytułu łącznikiem do innej linijki, aby wykryło to jako jeden nagłówek
                        if not current_text_parts and current_title:
                            current_title = f"{current_title} {text}"
                        else:
                            #Aby uznane było coś za rozdział, to musi mieć jakąś treść
                            if current_text_parts:
                                full_content = " ".join(current_text_parts).strip()
                                if len(full_content) > 5:
                                    blocks.append(ChapterBlock(
                                        id=block_id,
                                        title=current_title,
                                        content=full_content
                                    ))
                                    block_id += 1
                            
                            current_title = text
                            current_text_parts = []
                    else:
                        #Tekst dodany tylko, gdy jest jakiś nagłówek
                        if current_title: 
                            current_text_parts.append(text)

    #dodanie ostatniego bloku
    if current_title and current_text_parts:
        blocks.append(ChapterBlock(
            id=block_id,
            title=current_title,
            content=" ".join(current_text_parts).strip()
        ))

    doc.close()
    return blocks


#DO TESTOWANIA
#def save_blocks_to_txt(blocks_list, output_file):
 #   with open(output_file, "w", encoding="utf-8") as f:
  #      for block in blocks_list:
   #         f.write(f"Blok numer {block.id} : {block.title}\n")
    #        f.write("="*30 + "\n")
     #       f.write(f"Tekst: {block.content}\n")
      #      f.write("\n" + "*"*50 + "\n\n")

#if __name__ == "__main__":
 #   INPUT_PDF = "./prace/ch_inz_v31.pdf" 
  #  OUTPUT_TXT = "output_blokow.txt"
#
 #   extracted_blocks = get_content(INPUT_PDF)
  #  save_blocks_to_txt(extracted_blocks, OUTPUT_TXT)
   # 
    #print(f"Wykryto {len(extracted_blocks)}")
