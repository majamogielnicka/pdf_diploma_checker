import requests
from pathlib import Path
from text_extraction import get_content

MODEL_PL = "SpeakLeash/bielik-7b-instruct-v0.1-gguf:latest"
MODEL_EN = "qwen2.5:latest"

prompt_pl = f"""
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

        Tekst:"""

def get_purpose(path, prompt, model):
    text = get_content(path)

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {file_path}")

    prompt = prompt +text

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


def main():
    print(get_purpose("src/theses/doro.pdf", prompt_pl, MODEL_PL))


if __name__ == "__main__":
    main()