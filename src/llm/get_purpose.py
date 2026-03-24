import requests
from get_content import get_text

path, language = "src/theses/doro.pdf", "pl"

MODEL_PL = "SpeakLeash/bielik-7b-instruct-v0.1-gguf:latest"
MODEL_EN = "qwen2.5:latest"

PROMPT_PL = f"""
Przeczytaj poniższy tekst pracy dyplomowej i wywnioskuj główne zamierzenie autora.

Wymagania:
- odpowiedź wyłącznie po polsku
- dokładnie jedno zdanie
- forma rzeczowa i bezosobowa
- zacznij od formy typu: "Stworzenie...", "Opracowanie...", "Zaprojektowanie..."
- nie używaj form typu: "celem było", "autor chciał", "głównym zamierzeniem było"
- nie twórz listy
- nie streszczaj rozdziałów
- nie cytuj tekstu dosłownie
- nie dodawaj informacji spoza tekstu
- zwróć tylko jedno końcowe zdanie

Tekst:
"""

PROMPT_EN = f"""
Read the following thesis text and infer the author's main purpose.

Requirements:
- answer only in English
- exactly one sentence
- factual and impersonal style
- start with a form such as: "Development...", "Design...", "Implementation..."
- do not use phrases like: "the aim was", "the author wanted", "the main purpose was"
- do not create a list
- do not summarize chapters
- do not quote the text literally
- do not add information not present in the text
- return only one final sentence

Text:
"""

FINAL_PROMPT_PL = """
Na podstawie poniższych częściowych opisów głównego zamierzenia autora pracy dyplomowej
wywnioskuj jedno końcowe zdanie opisujące główne zamierzenie całej pracy.

Wymagania:
- odpowiedź wyłącznie po polsku
- dokładnie jedno zdanie
- forma rzeczowa i bezosobowa
- zacznij od formy typu: "Stworzenie...", "Opracowanie...", "Zaprojektowanie..."
- nie używaj form typu: "celem było", "autor chciał", "głównym zamierzeniem było"
- nie twórz listy
- nie dodawaj informacji spoza podanych opisów
- zwróć tylko jedno końcowe zdanie

Częściowe opisy:
"""

FINAL_PROMPT_EN = """
Based on the partial descriptions below, infer one final sentence describing
the main purpose of the whole thesis.

Requirements:
- answer only in English
- exactly one sentence
- factual and impersonal style
- start with a form such as: "Development...", "Design...", "Implementation..."
- do not use phrases like: "the aim was", "the author wanted", "the main purpose was"
- do not create a list
- do not add information not present in the descriptions
- return only one final sentence

Partial descriptions:
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

def ask_ollama(prompt, model):
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 1000,
                "top_p": 0.3
            }
        },
        timeout=600
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()

def gen_purpose(path, prompt, model, final_prompt):
    text = get_text(path)

    if isinstance(text, list):
        text = "\n".join(text)
    else:
        text = str(text)

    chunks = chunk_text(text, chunk_size=3000)

    partial_purposes = []

    try:
        for chunk in chunks:
            chunk_prompt = prompt + chunk
            partial_result = ask_ollama(chunk_prompt, model)
            partial_purposes.append(partial_result)

        merged_partial_purposes = "\n".join(
            f"- {purpose}" for purpose in partial_purposes
        )

        final_result = ask_ollama(final_prompt + merged_partial_purposes, model)
        return final_result

    except requests.exceptions.ReadTimeout:
        return "Błąd: model nie odpowiedział na czas."
    except requests.exceptions.ConnectionError:
        return "Błąd: nie udało się połączyć z Ollamą."
    except requests.exceptions.HTTPError as e:
        return f"Błąd HTTP: {e}"
    except Exception as e:
        return f"Błąd: {e}"

def get_purpose(path, language):
    if language == "pl":
        model = MODEL_PL
        prompt = PROMPT_PL
        final_prompt = FINAL_PROMPT_PL
    elif language == "en":
        model = MODEL_EN
        prompt = PROMPT_EN
        final_prompt = FINAL_PROMPT_EN
    else:
        return "Błąd: nieobsługiwany język."

    return gen_purpose(path, prompt, model, final_prompt)

def main():
    print(get_purpose(path, language))

if __name__ == "__main__":
    main()