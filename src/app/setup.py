import os
import subprocess
from PySide6.QtWidgets import QProgressDialog
from huggingface_hub import hf_hub_download
from PySide6.QtCore import Qt
import ssl
import ctypes

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TQDM_DISABLE"] = "True"

def check_and_download_requirements(parent=None):
    os.environ["TQDM_DISABLE"] = "True"
    try:
        subprocess.run(["java", "-version"], check=True, capture_output=True)
    except:
        print("Błąd: Java nie jest zainstalowana.")

    model_dir = os.path.join(os.path.expanduser("~"), "models", "gemma3_12b")
    model_file = "google_gemma-3-12b-it-Q4_K_M.gguf"
    full_model_path = os.path.join(model_dir, model_file)
    
    if not os.path.exists(full_model_path):
        progress = QProgressDialog("Pobieranie modelu AI (to może potrwać)...", None, 0, 100, parent)
        progress.setWindowTitle("Pierwsze uruchomienie")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        
        import QApplication
        if QApplication.instance():
            QApplication.instance().processEvents()

        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
            
        try:
            hf_hub_download(
                repo_id="bartowski/google_gemma-3-12b-it-GGUF",
                filename=model_file,
                local_dir=model_dir,
                local_dir_use_symlinks=False
            )
        except Exception as e:
            ctypes.windll.user32.MessageBoxW(0, f"Błąd pobierania modelu: {e}", "Błąd Krytyczny", 0x10)
            return False
        finally:
            progress.setValue(100)

    try:
        import pl_core_news_lg
    except ImportError:
        import spacy
        spacy.cli.download("pl_core_news_lg")
        
    return True