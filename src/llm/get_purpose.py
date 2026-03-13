import requests
from pathlib import Path
from get_content import get_text

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

def gen_purpose(path, prompt, model):
    text = get_text(path)

    if isinstance(text, list):
        text = "\n".join(text)
    else:
        text = str(text)

    prompt = prompt + text

    try:
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

        result = resp.json()["response"].strip()
        return result

    except requests.exceptions.ReadTimeout:
        return "Błąd: model nie odpowiedział na czas."
    except requests.exceptions.ConnectionError:
        return "Błąd: nie udało się połączyć z Ollamą."
    except requests.exceptions.HTTPError as e:
        return f"Błąd HTTP: {e}"
    except Exception as e:
        return f"Błąd: {e}"

def get_purpose(path, language):
    if language=="pl":
        model = MODEL_PL
        prompt = PROMPT_PL
    elif language == "en":
        model = MODEL_EN
        prompt = PROMPT_EN
    return gen_purpose(path, prompt, model)

def main():
    print(get_purpose("src/theses/doro.pdf", "pl"))

if __name__ == "__main__":
    main()