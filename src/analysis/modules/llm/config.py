from pathlib import Path

"""
Skrypt zawiera wszystkie niezbędne konfiguracje ścieżek do modeli
do analizy merytorycznej. Uruchamiany jako skrypt główny pozwala sprawdzić
czy wszystko jest poprawnie skonfigurowane
Skrypt powstał w celu jednego importu dla wszystkich skryptów i prostej konfiguracji w jednym pliku, 
wraz ze sprawdzeniem poprawności ścieżek
"""

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
OUTPUT_DIR = PROJECT_ROOT / "src" / "analysis" / "modules" / "llm" / "wyniki"

#JEDYNE 3 LINIJKI DO ZMIANY, JEŚLI URUCHAMIASZ
# MODEL_PATH = Path.home() / "models" / "gemma3_12b" / "google_gemma-3-12b-it-Q4_K_M.gguf"
MODEL_PATH = SRC_DIR / "models" / "gemma-3-12b-it-Q4_K_M.gguf"
LLAVA_MODEL_PATH = SRC_DIR / "models" / "llava-v1.6-mistral-7b.Q4_K_M.gguf"
LLAVA_MMPROJ_PATH = SRC_DIR / "models" / "mmproj-model-f16.gguf"
THESIS_PATH = PROJECT_ROOT / "data" / "most_important" / "jabi.pdf"
LANGUAGE = "pl" #LUB "en"

if __name__ == "__main__":
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"BASE_DIR_EXISTS: {BASE_DIR.exists()}")

    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"PROJECT_ROOT_EXISTS: {PROJECT_ROOT.exists()}")

    print(f"SRC_DIR: {SRC_DIR}")
    print(f"SRC_DIR_EXISTS: {SRC_DIR.exists()}")

    print(f"MODEL_PATH: {MODEL_PATH}")
    print(f"MODEL_EXISTS: {MODEL_PATH.exists()}")

    print(f"THESIS_PATH: {THESIS_PATH}")
    print(f"THESIS_EXISTS: {THESIS_PATH.exists()}")

    print(f"OUTPUT_DIR: {OUTPUT_DIR}")
    print(f"OUTPUT_DIR_EXISTS: {OUTPUT_DIR.exists()}")