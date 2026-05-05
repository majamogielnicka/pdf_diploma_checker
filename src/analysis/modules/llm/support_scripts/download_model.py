from pathlib import Path

from huggingface_hub import hf_hub_download

"""
Skrypt pobiera model Gemma 3 12B GGUF używany w projekcie.
Model zostanie zapisany w ~/models/gemma3_12b.
Po pobraniu ścieżkę do modelu można wpisać w config.py.
"""

MODEL_REPO_ID = "bartowski/google_gemma-3-12b-it-GGUF"
MODEL_FILENAME = "google_gemma-3-12b-it-Q4_K_M.gguf"

LOCAL_MODELS_DIR = Path.home() / "models"
MODEL_DIR = LOCAL_MODELS_DIR / "gemma3_12b"


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    model_path = hf_hub_download(
        repo_id=MODEL_REPO_ID,
        filename=MODEL_FILENAME,
        local_dir=str(MODEL_DIR),
        local_dir_use_symlinks=False,
    )

    print(f"Model zapisano do: {model_path}")


if __name__ == "__main__":
    main()