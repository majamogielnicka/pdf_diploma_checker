import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

try:
    from analysis.modules.llm.get_subtitles import extract_subtitles_from_pdf
except Exception:
    from get_subtitles import extract_subtitles_from_pdf

PDF_PATH = PROJECT_ROOT / "data" / "doro.pdf"
MODEL_DIR = BASE_DIR / "models" / "gemma3"

PROMPT_SYSTEM_PL = (
    "Odpowiadasz po polsku. "
    "Masz zwrócić dokładnie jedno pełne zdanie streszczenia wyłącznie na podstawie podanego tekstu. "
    "Zachowaj terminologię techniczną z tekstu. "
    "Nie upraszczaj nazw metod i nie zastępuj ich własnymi określeniami. "
    "Nie dodawaj informacji spoza tekstu. "
    "Nie używaj markdownu, kodu, list, nagłówków ani etykiet."
)

PROMPT_SYSTEM_EN = (
    "Respond in English. "
    "Return exactly one complete summary sentence based only on the provided text. "
    "Do not add any information not present in the text. "
    "Do not use markdown, code, lists, headings, or labels."
)

MAX_FRAGMENT_CHARS = 2200
MAX_NEW_TOKENS = 96

_TOKENIZER = None
_MODEL = None


def normalize_text(text):
    if not text:
        return ""
    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def prepare_fragment(fragment):
    text = normalize_text(fragment)
    if not text:
        return ""

    if len(text) <= MAX_FRAGMENT_CHARS:
        return text

    cut = text[:MAX_FRAGMENT_CHARS]

    last_dot = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if last_dot > int(MAX_FRAGMENT_CHARS * 0.6):
        return cut[: last_dot + 1].strip()

    last_space = cut.rfind(" ")
    if last_space > 0:
        return cut[:last_space].strip()

    return cut.strip()


def get_system_prompt(language):
    if language == "pl":
        return PROMPT_SYSTEM_PL
    if language == "en":
        return PROMPT_SYSTEM_EN
    raise ValueError("Nieobsługiwany język")


def get_model():
    global _TOKENIZER, _MODEL

    if _TOKENIZER is None or _MODEL is None:
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        _TOKENIZER = AutoTokenizer.from_pretrained(str(MODEL_DIR))
        _MODEL = AutoModelForCausalLM.from_pretrained(
            str(MODEL_DIR),
            torch_dtype=dtype,
            device_map="auto"
        )

        if _TOKENIZER.pad_token_id is None:
            _TOKENIZER.pad_token_id = 0

    return _TOKENIZER, _MODEL


def build_prompt(fragment, language, tokenizer):
    system_prompt = get_system_prompt(language)

    user_prompt = (
        "Streść poniższy fragment w jednym zdaniu:\n\n"
        f"{fragment}"
        if language == "pl"
        else
        "Summarize the following fragment in one sentence:\n\n"
        f"{fragment}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )


def get_summary(fragment, language):
    fragment = prepare_fragment(fragment)
    if not fragment:
        return "[PUSTY FRAGMENT]"

    tokenizer, model = get_model()
    prompt_text = build_prompt(fragment, language, tokenizer)

    inputs = tokenizer(prompt_text, return_tensors="pt")
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    eos_token_id = model.config.eos_token_id
    pad_token_id = tokenizer.pad_token_id

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            repetition_penalty=1.05,
            eos_token_id=eos_token_id,
            pad_token_id=pad_token_id,
            use_cache=True
        )

    generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
    result = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    return result or "[BRAK ODPOWIEDZI MODELU]"


def get_summaries(subtitles, language):
    summaries = []

    for i, sub in enumerate(subtitles, start=1):
        content = normalize_text(sub.get("content") or "")
        display = sub.get("display")
        number = sub.get("number")
        title = sub.get("title")

        if not display:
            display = f"{number or ''} {title or ''}".strip() or f"Sekcja {i}"

        if not content:
            summaries.append({
                "index": i,
                "number": number,
                "title": title,
                "display": display,
                "content": content,
                "summary": "[BRAK TREŚCI W SEKCJI]"
            })
            print(f"{i}/{len(subtitles)} - {display} -> BRAK TREŚCI")
            continue

        try:
            summary = get_summary(content, language)
        except Exception as e:
            summary = f"[BŁĄD GENEROWANIA: {e}]"

        summaries.append({
            "index": i,
            "number": number,
            "title": title,
            "display": display,
            "content": content,
            "summary": summary
        })

        print(f"{i}/{len(subtitles)} - {display}")

    return summaries


def summarize_subtitles(pdf_path, subtitles=None, language="pl"):
    pdf_path = Path(pdf_path)

    if subtitles is None:
        subtitles = extract_subtitles_from_pdf(pdf_path)

    return get_summaries(subtitles, language)


generate_summaries = summarize_subtitles


def print_summaries(summaries):
    if not summaries:
        print("Brak")
        return

    for item in summaries:
        print(item["display"])
        print("SUMMARY:")
        print(item["summary"])
        print()
        print("-" * 80)


def gen_summaries_doc():
    selected_pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_PATH
    language = sys.argv[2] if len(sys.argv) > 2 else "pl"

    if not selected_pdf_path.exists():
        print(f"Błąd: plik nie istnieje: {selected_pdf_path}")
        return

    if not MODEL_DIR.exists():
        print(f"Błąd: model nie istnieje: {MODEL_DIR}")
        return

    subtitles = extract_subtitles_from_pdf(selected_pdf_path)

    if not subtitles:
        print("Nie udało się wyciągnąć nagłówków / fragmentów z PDF.")
        return

    print(f"Wykryto nagłówków: {len(subtitles)}")

    summaries = get_summaries(subtitles, language)

    print()
    print_summaries(summaries)


def main():
    test_fragment = """
    Sieć piramidy cech (ang. Feature Pyramid Network – FPN) to ekstraktor cech zaprojektowany z myślą
    o detekcji obiektów w różnych skalach. Jego działanie można rozdzielić na dwie ścieżki, bottom-up i
    top-down. Pierwsza z nich, tj. bottom-up, przy użyciu sieci konwolucyjnych tworzy kolejne poziomy cech
    o rosnącym stopniu abstrakcji. W miarę poruszania się w górę tej ścieżki, rozdzielczość przestrzenna
    maleje, co pozwala na detekcję coraz bardziej złożonych struktur i obiektów. Poszczególne poziomy cech
    wykorzystywane są w drugiej ścieżce, która rozpoczyna się od najwyższego poziomu i stosuje na nim filtr
    konwolucyjny 1x1 i tym samym tworzy najwyższą warstwę cech o mniejsze gęstości. Dla tak utworzonej
    mapy cech wykonuje się operacje upsamplingu w celu zwiększenia jej rozmiaru. Następnie powiększona
    mapa cech łączona jest z odpowiadającą jej mapą cech ze ścieżki bottom-up z zastosowanym na niej
    filtrem konwolucyjny 1x1, rys. 3.3. Taki proces powtarzany jest dla kolejnych poziomów piramidy aż do
    drugiego poziomu licząc od dołu. Na utworzonych mapach cech ścieżki top-down stosuje się dodatkowo
    filtr konwolucyjny o rozmiarze 3x3 w celu redukcji efektu aliasingu.
    FPN nie odpowiada za detekcje obiektów, a jedynie przygotowuje mapy cech gotowe do wyko-
    rzystania w tym celu. Jest to alternatywne podejscie do piramidy obrazów z cechami (ang. Featurized
    image pyramid), polegającego na osobnym przetwarzeniu obrazów w różnych skalach. W tym kontekscie
    FPN pozwala ograniczyć potrzebny czas i pamięć na utworzenie map cech [5]
    """

    language = "pl"

    if not MODEL_DIR.exists():
        print(f"Błąd: model nie istnieje: {MODEL_DIR}")
        return

    summary = get_summary(test_fragment, language)

    print("FRAGMENT:")
    print(test_fragment.strip())
    print()
    print("SUMMARY:")
    print(summary)


if __name__ == "__main__":
    main()