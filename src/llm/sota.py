import requests
import json
from get_content import get_text 

MODEL_PL = "SpeakLeash/bielik-11b-v2.3-instruct:Q4_K_M"
MODEL_EN = "qwen2.5:latest"  

CONTEXT_PL = [
    "Odwołując się do obecnej wiedzy",
    "Zgodnie z wynikami badań",
    "W publikacji autora [X] wykazano",
    "Jak podaje literatura przedmiotu",
    "bazując na obecnych odkryciach", 
    "zgodnie z najnowszymi badaniami",
    "obecny stan wiedzy",
    "współczesne metody",
    "W oparciu o analizę źródeł",
    "Przegląd dotychczasowych odkryć wskazuje",
    "Autorzy tacy jak [Nazwisko] sugerują",
    "Stan wiedzy na rok [Data] definiuje",
    "Według klasyfikacji zaproponowanej przez",
    "W badaniach nad zjawiskiem [Nazwa] zauważono"
]

CONTEXT_EN = [
    "Referring to current knowledge",
    "According to the research results",
    "In the publication of author [X], it was shown",
    "As stated in the literature",
    "Based on current discoveries",
    "In accordance with the latest research",
    "Current state of knowledge",
    "Modern methods",
    "Based on the analysis of sources",
    "The review of previous findings indicates",
    "Authors such as [Name] suggest",
    "The state of knowledge as of [Date] defines",
    "According to the classification proposed by",
    "In studies on the phenomenon of [Name], it was noted"
]

PROMPT_PL_TEMPLATE = """Jesteś ekspertem analizującym prace dyplomowe. Szukasz fragmentów stanowiących SOTA (State of the Art) i przegląd literatury.

Zasady wyszukiwania:
1. Szukaj zdań będących odwołaniami do źródeł (np. nazwiska, daty, instytucje jak IASP).
2. Szukaj zdań opisujących współczesne standardy i wyniki badań.
3. Kopiuj cytaty DOKŁADNIE, zachowując przypisy (np. [5]).

UWAGA: W raporcie końcowym NIE umieszczaj fraz, które podałem Ci poniżej jako przykłady. Szukaj ich odpowiedników TYLKO w dostarczonym tekście pracy.

Przykładowe frazy pomocnicze (wzorce):
{context}

Wymagania techniczne:
- Format wyjściowy: JSON {{"znalezione_zdania": ["cytat 1", "cytat 2"]}}.
- Jeśli nic nie znajdziesz: {{"znalezione_zdania": []}}.
- Pomiń listę pozycji w bibliografii końcowej.

Tekst do analizy:
{text}
"""

PROMPT_EN_TEMPLATE = """You are an expert analyzing academic theses. You are looking for fragments representing SOTA (State of the Art) and literature review.

Search rules:
1. Look for sentences that are references to sources (e.g., names, dates, institutions like IASP).
2. Look for sentences describing modern standards and research results.
3. Copy quotes EXACTLY, preserving citations (e.g., [5]).

ATTENTION: In the final report, do NOT include the phrases I provided below as examples. Look for their equivalents ONLY within the provided text of the thesis.

Example helper phrases (patterns):
{context}

Technical requirements:
- Output format: JSON {{"found_sentences": ["quote 1", "quote 2"]}}.
- If nothing is found: {{"found_sentences": []}}.
- Skip the bibliography/reference list at the end.

Text to analyze:
{text}
"""

def chunk_text(text, chunk_size=3000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_length += len(word) + 1
        if current_length > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word) + 1
        else:
            current_chunk.append(word)
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

def extract_sota_from_chunk(text_chunk, language):
    if language == "pl":
        model = MODEL_PL
        context_str = "\n".join([f"- {c}" for c in CONTEXT_PL])
        prompt = PROMPT_PL_TEMPLATE.format(context=context_str, text=text_chunk)
        json_key = "znalezione_zdania"
        patterns_to_remove = CONTEXT_PL
    else:
        model = MODEL_EN
        context_str = "\n".join([f"- {c}" for c in CONTEXT_EN])
        prompt = PROMPT_EN_TEMPLATE.format(context=context_str, text=text_chunk)
        json_key = "found_sentences"
        patterns_to_remove = CONTEXT_EN

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json", 
                "options": {
                    "temperature": 0.0,
                    "top_p": 0.1
                }
            },
            timeout=120
        )
        resp.raise_for_status()
        
        response_text = resp.json()["response"]
        data = json.loads(response_text)
        raw_sentences = data.get(json_key, [])
        
        clean_sentences = [
            s for s in raw_sentences 
            if s not in patterns_to_remove 
            and "[X]" not in s 
            and "[Nazwisko]" not in s
            and "[Data]" not in s
            and "[Nazwa]" not in s
        ]
        
        return clean_sentences
        
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"[Błąd w fragmencie]: {e}")
        return []

def analyze_thesis_sota(path, language):
    print(f"Rozpoczynam analizę pliku: {path} (Język: {language})")
    full_text = get_text(path)
    
    chunks = chunk_text(full_text, chunk_size=3000)
    print(f"Tekst podzielono na {len(chunks)} fragmentów. Przeszukuję...")

    all_found_sota = []

    for i, chunk in enumerate(chunks):
        print(f"  Analiza fragmentu {i+1}/{len(chunks)}...")
        sentences = extract_sota_from_chunk(chunk, language)
        if sentences:
            all_found_sota.extend(sentences)

    print("\n" + "="*50)
    print(f"RAPORT SOTA DLA: {path}")
    print(f"Liczba znalezionych odwołań: {len(all_found_sota)}")
    print("="*50)
    
    if all_found_sota:
        for idx, sentence in enumerate(all_found_sota, 1):
            print(f"{idx}. \"{sentence}\"")
    else:
        print("Nie znaleziono żadnych odwołań do SOTA w tej pracy.")

if __name__ == "__main__":
    analyze_thesis_sota("src/theses/doro.pdf", "pl")