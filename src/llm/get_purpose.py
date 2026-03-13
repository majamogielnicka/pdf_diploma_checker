import requests
from pathlib import Path

MODEL = "SpeakLeash/bielik-7b-instruct-v0.1-gguf:latest"


def get_summary(path):
    """
    Generuje jednozdaniowe podsumowanie tekstu pracy dyplomowej przy użyciu modelu LLM.

    Args:
        path: Ścieżka do pliku tekstowego (.txt) z treścią pracy.

    Returns:
        Jedno zdanie w języku polskim określające główne zamierzenie autora.

    Raises:
        FileNotFoundError: Gdy plik pod wskazany adresem nie istnieje.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {file_path}")

    full_text = file_path.read_text(encoding="utf-8").strip()

    prompt = f"""
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
        {full_text}
        """

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL,
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


def main():
    base_dir = Path(__file__).resolve().parent
    plain_text_path = base_dir / "plain_text.txt"
    print(get_summary(plain_text_path))


if __name__ == "__main__":
    main()