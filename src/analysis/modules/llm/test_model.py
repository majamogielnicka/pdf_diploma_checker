from pathlib import Path
from llama_cpp import Llama

# ===== KONFIGURACJA =====
MODEL_PATH = Path.home() / "models" / "gemma3v2" / "gemma-1.1-7b-it-Q4_K_M.gguf"

N_CTX = 2048
MAX_TOKENS = 80
TEMPERATURE = 0.0
TOP_P = 0.2
REPEAT_PENALTY = 1.1
N_GPU_LAYERS = 0
N_THREADS = None

MODE = "plain"   # dla Gemmy lepiej najpierw testować plain

# ===== WKLEJANY FRAGMENT =====
FRAGMENT = """
Algorytmy rozpoznawania twarzy, używane w narzędziu, muszą być w stanie skutecznie identyfikować
unikalne twarze, aby nie było wątpliwości co do ich właściciela. Tylko w ten sposób będziemy w sta-
nie prawidłowo szacować pozycję i prędkość poszczególnych twarzy, co jest konieczne do usunięcia
niepewności pomiarowych i szumów detektora Haara.
Wstępne założenie narzędzia sugeruje możliwość występowania nawet kilku twarzy badanych
lub kilku twarzy w tle, które powinny być poprawnie klasyfikowane jako różne osoby. Efektywne wy-
korzystanie zasobów obliczeniowych jest kluczowe dla optymalnej pracy narzędzia na urządzeniach
mobilnych. W przypadku, gdy w kadrze obrazu pojawią się osoby trzecie, które nie są przedmiotem ana-
lizy, wystąpi niepotrzebne zużywanie mocy obliczeniowej przez model rozpoznawania emocji, co może
prowadzić do opóźnień w przetwarzaniu klatki. Wysoka dokładność modelu rozpoznawania twarzy spo-
woduje redukcję w niepotrzebnych predykcjach.
"""

PROMPT_PL = (
    "Napisz jedno zdanie po polsku streszczające główną myśl fragmentu. "
    "Nie dodawaj informacji spoza tekstu. "
    "Zwróć tylko jedno zdanie.\n"
)


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def build_plain_prompt(fragment: str) -> str:
    return (
        f"{PROMPT_PL}\n"
        f"FRAGMENT:\n{fragment}\n\n"
        f"STRESZCZENIE:\n"
    )


def run_plain(llm: Llama, fragment: str) -> str:
    prompt = build_plain_prompt(fragment)

    output = llm(
        prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        repeat_penalty=REPEAT_PENALTY,
        stop=["\n\n", "FRAGMENT:", "STRESZCZENIE:"],
        echo=False,
    )

    return output["choices"][0]["text"].strip()


def run_chat(llm: Llama, fragment: str) -> str:
    output = llm.create_chat_completion(
        messages=[
            {
                "role": "user",
                "content": (
                    f"{PROMPT_PL}\n\n"
                    f"FRAGMENT:\n{fragment}"
                ),
            },
        ],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        repeat_penalty=REPEAT_PENALTY,
        stop=["\n\n"],
    )

    return output["choices"][0]["message"]["content"].strip()


def main():
    fragment = normalize_text(FRAGMENT)

    if not fragment:
        print("Błąd: pusty fragment.")
        return

    if not MODEL_PATH.exists():
        print(f"Błąd: model nie istnieje: {MODEL_PATH}")
        return

    llm = Llama(
        model_path=str(MODEL_PATH),
        n_ctx=N_CTX,
        n_threads=N_THREADS,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False,
    )

    print("=== FRAGMENT ===")
    print(fragment)
    print()

    print(f"=== TRYB: {MODE} ===")

    if MODE == "plain":
        result = run_plain(llm, fragment)
    elif MODE == "chat":
        result = run_chat(llm, fragment)
    else:
        print("Błąd: MODE musi być 'plain' albo 'chat'.")
        return

    print("=== STRESZCZENIE ===")
    print(result)


if __name__ == "__main__":
    main()