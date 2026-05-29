import os
import subprocess
import spacy

def check_and_download_requirements(parent=None):
    os.environ["TQDM_DISABLE"] = "True"
    try:
        subprocess.run(["java", "-version"], check=True, capture_output=True)
    except Exception:
        print("Błąd: Java nie jest zainstalowana.")

    try:
        import pl_core_news_lg
    except ImportError:
        print("Pobieranie pakietu języka polskiego SpaCy...")
        spacy.cli.download("pl_core_news_lg")

    try:
        import en_core_web_lg
    except ImportError:
        print("Pobieranie pakietu języka angielskiego SpaCy...")
        spacy.cli.download("en_core_web_lg")
        
    return True