import os
import subprocess
from PySide6.QtWidgets import QProgressDialog
from huggingface_hub import hf_hub_download
from PySide6.QtCore import Qt

def check_and_download_requirements(parent=None):
    try:
        subprocess.run(["java", "-version"], check=True, capture_output=True)
    except:
        print("Błąd: Java nie jest zainstalowana.")

    model_path = os.path.join(os.path.expanduser("~"), "models", "gemma3_12b", "google_gemma-3-12b-it-Q4_K_M.gguf")
    
    if not os.path.exists(model_path):
        progress = QProgressDialog("Pobieranie modelu AI (to może potrwać)...", "Anuluj", 0, 100, parent)
        progress.setWindowTitle("Pierwsze uruchomienie")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        hf_hub_download(
            repo_id="bartowski/google_gemma-3-12b-it-GGUF",
            filename="google_gemma-3-12b-it-Q4_K_M.gguf",
            local_dir=os.path.dirname(model_path)
        )
        progress.setValue(100)

    try:
        import pl_core_news_lg
    except ImportError:
        import spacy
        spacy.cli.download("pl_core_news_lg")
    return True