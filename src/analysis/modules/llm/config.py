import os
import sys
import json
from pathlib import Path

from common.path import resource_path


def get_app_dir():
    """
    Return the directory containing the application configuration.

    In development mode, this returns the project root directory.
    In a PyInstaller build, this returns the directory containing the executable.
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[4]


APP_DIR = get_app_dir()
APP_CONFIG_PATH = APP_DIR / "app_config.json"


def load_app_config():
    """
    Load app_config.json from the application directory.
    """

    if not APP_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Missing app_config.json: {APP_CONFIG_PATH}")

    with APP_CONFIG_PATH.open("r", encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("app_config.json must contain a JSON object.")

    return config


_CONFIG = load_app_config()


DEVICE = str(_CONFIG["device"]).lower().strip()
N_GPU_LAYERS = int(_CONFIG["n_gpu_layers"])

print("[CONFIG] N_GPU_LAYERS =", N_GPU_LAYERS)

MODEL_DIR = Path(str(_CONFIG["model_dir"])).expanduser()
LANGUAGE = str(_CONFIG.get("language", "pl")).lower().strip()

MODEL_PATH = MODEL_DIR / "gemma3_12b" / "google_gemma-3-12b-it-Q4_K_M.gguf"
LLAVA_MODEL_PATH = MODEL_DIR / "llava-v1.6-mistral-7b.Q4_K_M.gguf"
LLAVA_MMPROJ_PATH = MODEL_DIR / "mmproj-model-f16.gguf"

THESIS_DIR = Path(
    str(
        _CONFIG.get(
            "thesis_dir",
            Path.home() / "theses",
        )
    )
).expanduser()

THESIS_PATH = Path(
    str(
        _CONFIG.get(
            "thesis_path",
            APP_DIR / "src" / "app" / "jago.pdf",
        )
    )
).expanduser()

OUTPUT_DIR = Path(
    str(
        _CONFIG.get(
            "output_dir",
            resource_path(os.path.join("analysis", "modules", "llm", "wyniki")),
        )
    )
).expanduser()

EMBEDDING_MODEL = str(
    _CONFIG.get(
        "embedding_model",
        "intfloat/multilingual-e5-large",
    )
)