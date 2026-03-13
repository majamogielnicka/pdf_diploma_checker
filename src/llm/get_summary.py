import requests

MODEL_PL = "SpeakLeash/bielik-7b-instruct-v0.1-gguf:latest"
MODEL_EN = "qwen2.5:latest"

fragment = """Ból ostry jest wywołany przez bezpośrednie uszkodzenie tkanek, lub bodźca, który
                uszkadza tkanki, co uruchamia nocyceptory. Jest to typ bólu, który pełni funkcję ochronną,
                powstaje w sytuacjach zagrożenia, po operacjach i oparzeniach. Ból ostry, jest
                krótkotrwałym odczuciem, ustępującym, gdy bodziec przestaje działać na ciało.
                W leczeniu bólu, stosuje się farmakoterapię opioidami, niesteroidowymi lekami
                przeciwzapalnymi, jak również blokady nerwowe.
                Cechuje się krótkim czasem trwania do 3 miesięcy, przeważnie jego lokalizacja
                i rozpoznanie jest łatwe, co ułatwia leczenie. Może mieć charakter na przykład rwący czy
                kłujący."""


prompt_pl = f"""Streść poniższy fragment w jednym zdaniu.
                Wymagania:
                - odpowiedź wyłącznie po polsku
                - max 1 zdanie
                - bez cytatów i bez wypunktowań
                - nie używaj angielskich słów
                - zachowaj sens, nie dodawaj informacji spoza fragmentu
                Fragment:
                """

def get_summary(fragment, model, prompt):

    """
    Generuje jednozdaniowe streszczenie fragmentu tekstu w języku polskim.

    Funkcja wysyła zapytanie do lokalnego serwera Ollama (http://localhost:11434), 
    wymuszając na modelu LLM specyficzny format odpowiedzi (jedno zdanie, bez list).

    Args:
        fragment: Surowy tekst, który ma zostać podsumowany.

    Returns:
        Jednozdaniowe streszczenie zwrócone przez model.

    Raises:
        requests.exceptions.RequestException: Występuje w przypadku problemów 
            z połączeniem z serwerem Ollama lub przekroczenia czasu (timeout).
    """

    prompt = prompt + fragment

    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()["response"]

def main():
    print(get_summary(fragment, MODEL_PL, prompt_pl))

if __name__ == "__main__":
    main()