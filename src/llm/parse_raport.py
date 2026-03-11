from pathlib import Path
import re


def detect_noise(text: str):
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