import os
import sys
from pathlib import Path

"""Central configuration for LLM analysis modules.

This module defines model paths and runtime settings shared by the
content-analysis pipeline. When executed directly, it prints a quick
configuration check for key paths.
"""

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
SRC_DIR = PROJECT_ROOT / "src"

for p in (PROJECT_ROOT, SRC_DIR):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

from common.path import resource_path

EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
OUTPUT_DIR = Path(resource_path(os.path.join("analysis", "modules", "llm", "wyniki")))
THESIS_DIR = Path.home() / "theses"

#JEDYNE 3 LINIJKI DO ZMIANY, JEŚLI URUCHAMIASZ
MODEL_PATH = Path.home() / "models" / "gemma3_12b" / "google_gemma-3-12b-it-Q4_K_M.gguf"
N_GPU_LAYERS = 25
LLAVA_MODEL_PATH=Path.home() / "models" / "llava-v1.6-mistral-7b.Q4_K_M.gguf"
LLAVA_MMPROJ_PATH=Path.home() / "models" / "mmproj-model-f16.gguf"

THESIS_PATH = THESIS_DIR / "jost2.pdf"
LANGUAGE = "en" #LUB "en"

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