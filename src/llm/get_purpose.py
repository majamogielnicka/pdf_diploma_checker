import requests
from pathlib import Path

from get_content import get_content, ChapterBlock

MODEL_PL = "SpeakLeash/bielik-7b-instruct-v0.1-gguf:latest"
MODEL_EN = "qwen2.5:latest"

PROMPT_PL = """
Przeczytaj poniższy rozdział pracy dyplomowej i wywnioskuj główne zamierzenie autora.

Wymagania:
- odpowiedź wyłącznie po polsku
- dokładnie jedno zdanie
- forma rzeczowa i bezosobowa
- zacznij od formy typu: "Stworzenie...", "Opracowanie...", "Zaprojektowanie..."
- nie używaj form typu: "celem było", "autor chciał", "głównym zamierzeniem było"
- nie twórz listy
- nie streszczaj rozdziału
- nie cytuj tekstu dosłownie
- nie dodawaj informacji spoza tekstu
- zwróć tylko jedno końcowe zdanie

Tytuł rozdziału: {title}
Treść rozdziału:
{content}
"""

PROMPT_EN = """
Read the following thesis chapter and infer the author's main purpose.

Requirements:
- answer only in English
- exactly one sentence
- factual and impersonal style
- start with a form such as: "Development...", "Design...", "Implementation..."
- do not use phrases like: "the aim was", "the author wanted", "the main purpose was"
- do not create a list
- do not summarize the chapter
- do not quote the text literally
- do not add information not present in the text
- return only one final sentence

Chapter title: {title}
Chapter content:
{content}
"""

def ask_ollama(prompt, model):
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 300,
                "top_p": 0.3
            }
        },
        timeout=600
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()

def find_purpose_chapter(blocks, language="pl"):
    valid_blocks = [
        block for block in blocks
        if block.title and block.content and len(block.content.strip()) > 100
    ]

    if language == "pl":
        exact_primary = ["cel pracy", "cele pracy"]
        primary_keywords = ["cel", "cele"]
        secondary_keywords = ["wstęp", "wprowadzenie"]
    else:
        exact_primary = [
            "goals of the study",
            "goal of the study",
            "study goals",
            "study goal",
            "objectives of the study",
            "objective of the study",
            "purpose of the study",
            "aim of the study"
        ]
        primary_keywords = ["goal", "goals", "objective", "objectives", "purpose", "aim"]
        secondary_keywords = ["introduction"]

    for block in valid_blocks:
        title_lower = block.title.lower().strip()
        if any(keyword in title_lower for keyword in exact_primary):
            return block

    for block in valid_blocks:
        title_lower = block.title.lower().strip()
        if any(keyword in title_lower for keyword in primary_keywords):
            return block

    for block in valid_blocks:
        title_lower = block.title.lower().strip()
        if any(keyword in title_lower for keyword in secondary_keywords):
            return block

    return valid_blocks[0] if valid_blocks else None

def generate_purpose_from_chapter(block: ChapterBlock, language: str):
    truncated_content = block.content[:6000]

    if language == "pl":
        model = MODEL_PL
        prompt = PROMPT_PL.format(
            title=block.title if block.title else "Brak",
            content=truncated_content
        )
    elif language == "en":
        model = MODEL_EN
        prompt = PROMPT_EN.format(
            title=block.title if block.title else "None",
            content=truncated_content
        )
    else:
        return "Błąd: nieobsługiwany język."

    try:
        return ask_ollama(prompt, model)
    except requests.exceptions.ReadTimeout:
        return "Błąd: model nie odpowiedział na czas."
    except requests.exceptions.ConnectionError:
        return "Błąd: nie udało się połączyć z Ollamą."
    except requests.exceptions.HTTPError as e:
        return f"Błąd HTTP: {e}"
    except Exception as e:
        return f"Błąd: {e}"

def get_purpose(path, language="pl"):
    blocks = get_content(path)
    purpose_block = find_purpose_chapter(blocks, language)

    if not purpose_block:
        return "Błąd: nie znaleziono odpowiedniego rozdziału."

    return generate_purpose_from_chapter(purpose_block, language)

def main():
    path = Path("src/theses/doro.pdf")
    language = "pl"
    print(get_purpose(path, language))

if __name__ == "__main__":
    main()