import json
from get_content import get_content
from extract_citations import extract_citations
from evaluate_sota import get_llm

PROMPT_EVALUATE_PL = """Jesteś ekspertem analizującym strukturę prac naukowych. 
Twoim zadaniem jest ocenić, czy podany rozdział stanowi SOTA (State of the Art / Przegląd literatury / Stan obecny).

Rozdział SOTA charakteryzuje się:
1. Odwołaniami do literatury przedmiotu i innych badań (np. [1], [2], nazwiska autorów).
2. Analizą i porównaniem istniejących na rynku lub w nauce rozwiązań, metod lub technologii.
3. Wskazywaniem luk w obecnej wiedzy lub opisywaniem historii problemu.
4. Jest to CIĄGŁY TEKST (narracja), a nie lista punktów, spis nagłówków czy bibliografia.

CZEGO UNIKAĆ (To NIE JEST SOTA):
- Rozdziały techniczne i organizacyjne (np. opis struktury pracy, podział ról w zespole, instrukcje obsługi, opis działania stworzonej aplikacji).
- Słowniki pojęć, wykazy skrótów, spisy tabel.
- Zwykłe wymienianie bibliografii bez narracji.

Tytuł ocenianego rozdziału: {title}
Fragment treści: {content}

Zwróć wynik WYŁĄCZNIE w formacie JSON o następującej strukturze:
{{
  "czy_sota": true lub false,
  "pewnosc_procentowa": liczba całkowita od 0 do 100,
  "uzasadnienie": "Krótkie, jednozdaniowe uzasadnienie decyzji"
}}
"""

PROMPT_EVALUATE_EN = """You are an expert analyzing the structure of academic papers.
Your task is to evaluate whether the provided chapter represents the SOTA (State of the Art / Literature Review / Current State).

A SOTA chapter is characterized by:
1. References to literature and other research (e.g., [1], [2], authors' names).
2. Analysis and comparison of existing solutions, methods, or technologies in the market or science.
3. Pointing out gaps in current knowledge or describing the history of the problem.
4. It is CONTINUOUS TEXT (narrative), not a bulleted list, table of contents, or bibliography.

WHAT TO AVOID (This is NOT SOTA):
- Technical and organizational chapters (e.g., description of thesis structure, division of roles, user manuals, application description).
- Glossaries, list of abbreviations, list of tables.
- Mere listing of bibliography without narrative.

Title of the evaluated chapter: {title}
Content snippet: {content}

Return the result EXCLUSIVELY in JSON format with the following structure:
{{
  "czy_sota": true or false,
  "pewnosc_procentowa": integer from 0 to 100,
  "uzasadnienie": "Short, one-sentence justification for the decision"
}}
"""

def get_sota_chapter(path: str, language: str = "pl"):
    """
    Skanuje pracę i zwraca tuple: (id, tytul, metoda_wyboru, liczba_cytowan).
    """
    blocks = get_content(path)
    if not blocks:
        return None, None, "Brak tekstu", 0

    if language == "pl":
        BLACKLIST = ["spis treści", "bibliografia", "spis rysunków", "spis tabel", "streszczenie", "abstract", "lista skrótów", "załącznik", "literatura", "indeks", "opis dyplomu", "oświadczenie", "opis pracy", "cel pracy", "wstęp", "zakończenie", "podsumowanie"]
        SOTA_KEYWORDS = ["przegląd literatury", "stan wiedzy", "state of the art", "sota", "przegląd rozwiązań", "istniejące rozwiązania", "analiza literatury", "podbudowa teoretyczna", "przegląd badań", "przegląd technologii", "stan obecny"]
    else:
        BLACKLIST = ["table of contents", "bibliography", "list of figures", "list of tables", "abstract", "abbreviations", "appendix", "references", "index", "declaration", "introduction", "conclusion", "summary", "thesis overview"]
        SOTA_KEYWORDS = ["literature review", "state of the art", "sota", "existing solutions", "related work", "background", "theoretical background", "technology review"]

    valid_blocks = [b for b in blocks if len(b.content) >= 200 and not any(bad in (b.title.lower() if b.title else "") for bad in BLACKLIST)]
    
    sota_chapter = None
    metoda = "Nie znaleziono"
    
    # KROK 1: Tytuł
    for block in valid_blocks:
        title_lower = block.title.lower() if block.title else ""
        if any(kw in title_lower for kw in SOTA_KEYWORDS):
            sota_chapter = block
            metoda = "KROK 1 (Słowa kluczowe w tytule)"
            break

    # KROK 2: Analiza AI
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

    # KROK 3: Zliczanie ilości cytowań
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
        return str(sota_chapter.id), str(sota_chapter.title or "Bez tytułu"), metoda, unique_citations
    
    return None, None, "Nie znaleziono", 0