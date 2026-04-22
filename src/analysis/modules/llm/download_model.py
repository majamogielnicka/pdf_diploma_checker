import sys
from pathlib import Path

from huggingface_hub import snapshot_download

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[3]
MODELS_DIR = BASE_DIR / "models"
MODEL_DIR = MODELS_DIR / "gemma3"

MODEL_ID = "google/gemma-3-1b-it"


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    local_path = snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(MODEL_DIR),
        local_dir_use_symlinks=False
    )

    print(f"Model zapisano do: {local_path}")


if __name__ == "__main__":
    main()