"""
Moduł do oczyszczania i ekstrakcji tekstu z raportów tekstowych.

Narzędzie parsuje pliki wejściowe, wyciąga fragmenty oznaczone markerem 'Tekst:',
usuwa szum (numery stron, fragmenty kodu) oraz naprawia błędy składu (np. dzielenie wyrazów).
"""

from pathlib import Path
import re


def detect_noise(text: str):

    """
    Sprawdza, czy podany fragment tekstu jest 'szumem' (niechcianą treścią).

    Za szum uznaje się:
    - Puste ciągi znaków.
    - Same cyfry (np. numery stron).
    - Linie zaczynające się od cyfr (np. spisy treści).
    - Fragmenty kodu źródłowego Pythona.

    Args:
        text: Fragment tekstu do analizy.

    Returns:
        True, jeśli tekst jest szumem i powinien zostać odrzucony. False w przeciwnym razie.
    """

    t = text.strip()

    if not t:
        return True

    if re.fullmatch(r"\d+", t):
        return True

    if re.match(r"^\d+\s+\w+", t):
        return True

    code_markers = [
        "class ",
        "def ",
        "return ",
        "self.",
        "__init__",
        "object):",
        "cosine(",
    ]
    if any(marker in t for marker in code_markers):
        return True

    return False


def extract_plain_text_from_report(input_path: str, output_path: str = "plain_text.txt"):

    """
    Wyciąga czysty tekst z raportu i zapisuje go do pliku.

    Proces obejmuje:
    1. Znalezienie bloków tekstu między tagiem 'Tekst:' a separatorem '---'.
    2. Usunięcie zbędnych nowej linii i spacji.
    3. Filtrację szumu za pomocą funkcji detect_noise.
    4. Łączenie wyrazów rozdzielonych dywizem (np. 'tek- st' -> 'tekst').

    Args:
        input_path: Ścieżka do pliku raportu wejściowego.
        output_path: Ścieżka, gdzie ma zostać zapisany wynik. Domyślnie 'plain_text.txt'.

    Returns:
        Oczyszczony, pełny tekst jako jeden ciąg znaków.

    Raises:
        FileNotFoundError: Jeśli plik wejściowy nie istnieje.
    """

    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku: {input_file}")

    content = input_file.read_text(encoding="utf-8")

    matches = re.findall(
        r"Tekst:\s*\n(.*?)\n-+",
        content,
        flags=re.DOTALL
    )

    fragments = []
    for fragment in matches:
        text = fragment.strip()
        text = text.replace("\n", " ").strip()

        if detect_noise(text):
            continue

        fragments.append(text)

    full_text = " ".join(fragments)

    full_text = re.sub(r"(\w)-\s+(\w)", r"\1\2", full_text)

    full_text = re.sub(r"\s+", " ", full_text).strip()

    output_file.write_text(full_text, encoding="utf-8")
    return full_text


def main():

    """Uruchamia proces ekstrakcji dla domyślnego pliku raportu."""

    base_dir = Path(__file__).resolve().parent 
    raport_path = base_dir / "raport.txt"
    plain_text_path = base_dir / "plain_text.txt"

    text = extract_plain_text_from_report(raport_path, plain_text_path)

    print("Gotowe")
    print(f"Wejście: {raport_path}")
    print(f"Wynik zapisano do: {plain_text_path}")
    print(f"Liczba znaków: {len(text)}")


if __name__ == "__main__":
    main()