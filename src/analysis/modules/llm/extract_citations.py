import re
from pathlib import Path
from get_content import get_content

NUMERIC_PATTERN = r'\[\s*\d+\s*(?:[,;\-–]\s*\d+\s*)*\]'
HARVARD_PATTERN = r'\([A-ZŚĆŻŹŁ][^()0-9]+(?:19|20)\d{2}[^()]*\)'
MLA_PATTERN = r'\([A-ZŚĆŻŹŁ][a-ząćęłńóśźż]+\s+\d{1,4}\)'
FOOTNOTE_PATTERN = r'(?:^|\n)\s*\d+[\.\)]?\s*[A-ZŚĆŻŹŁ]\.\s+[A-ZŚĆŻŹŁ][a-ząćęłńóśźż]+'
ALPHA_PATTERN = r'\[[A-Za-zŚĆŻŹŁąćęłńóśźż]{2,6}\d{2}[a-z]?\]'
ACM_PATTERN = r'\[[A-ZŚĆŻŹŁ][A-Za-zŚĆŻŹŁąćęłńóśźż\s\.\,]+?\s+(?:19|20)\d{2}\]'

def extract_citations(text):
    numeric = re.findall(NUMERIC_PATTERN, text)
    harvard = re.findall(HARVARD_PATTERN, text)
    mla = re.findall(MLA_PATTERN, text)
    footnotes = re.findall(FOOTNOTE_PATTERN, text)
    alpha = re.findall(ALPHA_PATTERN, text)
    acm = re.findall(ACM_PATTERN, text)
    
    footnotes_cleaned = [f.strip() for f in footnotes]
    
    all_citations = numeric + harvard + mla + footnotes_cleaned + alpha + acm
    return all_citations

def analyze_sota_citations(pdf_path, sota_ids, output_dir="."):
    output_lines = []
    output_lines.append(f"Wczytywanie pliku: {pdf_path}")
    
    blocks = get_content(pdf_path)
    
    total_citations = 0
    all_found_citations = []
    
    for block in blocks:
        if block.id in sota_ids:
            output_lines.append(f"\n--- Rozdział: {block.title} (ID: {block.id}) ---")
            
            citations = extract_citations(block.content)
            count = len(citations)
            total_citations += count
            
            if count > 0:
                output_lines.append(f"Znaleziono cytowań: {count}")
                
                unique_citations = sorted(set(citations))
                output_lines.append(f"Unikalnych przypisów: {len(unique_citations)}")
                
                for c in unique_citations:
                    c_clean = " ".join(c.split())
                    output_lines.append(f"  - {c_clean}")
                    
                all_found_citations.extend(citations)
            else:
                output_lines.append("Brak cytowań w tym rozdziale.")

    output_lines.append("\n")
    output_lines.append("PODSUMOWANIE SOTA:")
    output_lines.append(f"Przeszukano {len(sota_ids)} rozdziałów SOTA.")
    output_lines.append(f"Łączna liczba wszystkich wstawień cytowań: {total_citations}")
    
    global_unique = set(all_found_citations)
    output_lines.append(f"Łączna liczba unikalnych przypisów z całej pracy: {len(global_unique)}")

    summary_text = "\n".join(output_lines)
    print(summary_text)

    out_folder = Path(output_dir)
    out_folder.mkdir(parents=True, exist_ok=True)
    
    pdf_stem = Path(pdf_path).stem
    output_filename = out_folder / f"cytowania_{pdf_stem}.txt"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(summary_text)
        
    print(f"\nZapisano wyniki do pliku: {output_filename.absolute()}")