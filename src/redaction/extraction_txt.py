import fitz  
import os

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


def analyze_thesis(file_path):
    if not os.path.exists(file_path):
        print(f"Błąd: Nie znaleziono pliku '{file_path}'")
        return

    doc = fitz.open(file_path) # wczytanie pliku za pomocą pymupdf (fitz)
    with open("raport.txt", "w", encoding="utf-8") as f:   # wypisanie podstawowych informacji (w pliku .txt)
        print(f"--- ANALIZA PLIKU: {file_path} ---", file = f)
        print(f"Liczba stron: {len(doc)}", file = f)
        print("\n[1] Metadane dokumentu:", file = f)

    meta = doc.metadata
    with open("raport.txt", "a", encoding="utf-8") as f:   # wypisanie metadanych
        print(f"  - Tytuł: {meta.get('title')}", file = f)
        print(f"  - Autor: {meta.get('author')}", file = f)
        print(f"  - Narzędzie: {meta.get('creator')}", file = f)
        print(f"  - Data utworzenia: {meta.get('creationDate')}", file = f)

        print("\n[2] Podgląd bloków na 1. stronie (Struktura):", file = f)
        print(" ", file = f)
        f.write("-" * 30 + "\n") 

    with open("raport.txt", "a", encoding="utf-8") as f:    # wypisanie konkretnych bloczków
        for i in range(len(doc)):
            curr_page = doc[i]
            blocks = curr_page.get_text("blocks") # blocks zawiera informacje o bloczkach
        
            for j, b in enumerate(blocks):
                x0, y0, x1, y1, text, block_no, block_type = b # b[0] to wierzczhołek x0 bloczka; b[4] to tekst w bloczku itd

                #Obsługa niektórych LaTeX'ów
                if meta.get('creator')=='LaTeX with hyperref':
                    text = fix_latex(text)
            
                f.write(f"Strona: {i+1}, Blok na stronie: {j} (ID: {block_no})\n")
            
                f.write(f"Wierzchołki: "
                        f"LG:({round(x0)};{round(y0)}), "
                        f"PG:({round(x1)};{round(y0)}), "
                        f"LD:({round(x0)};{round(y1)}), "
                        f"PD:({round(x1)};{round(y1)})\n")
            
                f.write(f"Typ bloku: {'Tekst' if block_type == 0 else 'Grafika'}\n")
                f.write(f"Tekst:\n{text.strip()}\n")
                f.write("-" * 30 + "\n\n") 

    doc.close()

    

if __name__ == "__main__":
    MY_FILE = "prace/bm_inz_v1.pdf" # podaj nazwe PDF
    analyze_thesis(MY_FILE)
