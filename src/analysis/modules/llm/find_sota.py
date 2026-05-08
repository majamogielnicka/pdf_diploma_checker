import json
from extract_citations import extract_citations
from evaluate_sota import get_llm

PROMPT_EVALUATE_PL = """Jesteś ekspertem analizującym strukturę prac naukowych... [treść promptu]"""
PROMPT_EVALUATE_EN = """You are an expert analyzing the structure of academic papers... [treść promptu]"""

def get_sota_chapter(blocks: list, language: str = "pl"):
    """
    Skanuje przekazane bloki i zwraca tuple: (id, tytul, metoda_wyboru, liczba_cytowan, WYEKSTRAKTOWANY_TEKST).
    """
    if not blocks:
        return None, None, "Brak tekstu", 0, ""

    if language == "pl":
        BLACKLIST = ["spis treści", "bibliografia", "spis rysunków", "spis tabel", "streszczenie", "abstract", "lista skrótów", "załącznik", "literatura", "indeks", "opis dyplomu", "oświadczenie", "opis pracy", "cel pracy", "wstęp", "zakończenie", "podsumowanie"]
        SOTA_KEYWORDS = ["przegląd literatury", "stan wiedzy", "state of the art", "sota", "przegląd rozwiązań", "istniejące rozwiązania", "analiza literatury", "podbudowa teoretyczna", "przegląd badań", "przegląd technologii", "stan obecny"]
    else:
        BLACKLIST = ["table of contents", "bibliography", "list of figures", "list of tables", "abstract", "abbreviations", "appendix", "references", "index", "declaration", "introduction", "conclusion", "summary", "thesis overview"]
        SOTA_KEYWORDS = ["literature review", "state of the art", "sota", "existing solutions", "related work", "background", "theoretical background", "technology review"]

    valid_blocks = [b for b in blocks if len(b.content) >= 200 and not any(bad in (b.title.lower() if b.title else "") for bad in BLACKLIST)]
    
    sota_chapter = None
    metoda = "Nie znaleziono"
    
    for block in valid_blocks:
        title_lower = block.title.lower() if block.title else ""
        if any(kw in title_lower for kw in SOTA_KEYWORDS):
            sota_chapter = block
            metoda = "KROK 1 (Słowa kluczowe w tytule)"
            break

    if not sota_chapter:
        llm = get_llm()
        llm_candidates = []
        for block in valid_blocks:
            truncated_content = block.content[:4000]
            prompt = PROMPT_EVALUATE_PL.format(title=block.title or "Brak", content=truncated_content) if language == "pl" else PROMPT_EVALUATE_EN.format(title=block.title or "None", content=truncated_content)
            try:
                response = llm.create_chat_completion(
                    messages=[{"role": "system", "content": "Zwracaj JSON."}, {"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}, temperature=0.0
                )
                data = json.loads(response["choices"][0]["message"]["content"])
                score = data.get("pewnosc_procentowa", 0)
                if score >= 90 and data.get("czy_sota"):
                    llm_candidates.append({"block": block, "score": score})
            except: continue
        
        if llm_candidates:
            perfect = [c for c in llm_candidates if c["score"] == 100]
            if perfect:
                sota_chapter = perfect[0]["block"]
                metoda = "KROK 2 (Analiza AI - 100% pewności)"
            else:
                best = max(llm_candidates, key=lambda c: len(set(extract_citations(c["block"].content))))
                sota_chapter = best["block"]
                metoda = f"KROK 2 (Analiza AI - {best['score']}% + Cytowania)"

    if not sota_chapter:
        best_block = None
        max_c = -1
        for block in valid_blocks:
            c_count = len(set(extract_citations(block.content)))
            if c_count > max_c:
                max_c = c_count
                best_block = block
        if best_block and max_c > 0:
            sota_chapter = best_block
            metoda = "KROK 3 (Najwięcej cytowań)"

    if sota_chapter:
        unique_citations = len(set(extract_citations(sota_chapter.content)))
        return str(sota_chapter.id), str(sota_chapter.title or "Bez tytułu"), metoda, unique_citations, sota_chapter.content
    
    return None, None, "Nie znaleziono", 0, ""