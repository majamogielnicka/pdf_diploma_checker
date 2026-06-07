import sys
import json
from pathlib import Path


def get_app_dir():
    """
    Return the directory containing the application configuration.

    In development mode, this returns the project root directory.
    In a PyInstaller build, this returns the directory containing the executable.
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

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
            APP_DIR / "output",
        )
    )
).expanduser()

EMBEDDING_MODEL = str(
    _CONFIG.get(
        "embedding_model",
        "paraphrase-multilingual-MiniLM-L12-v2",
    )
)