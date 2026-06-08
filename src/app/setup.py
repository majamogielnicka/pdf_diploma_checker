import os
import subprocess
import spacy

def check_and_download_requirements(parent=None):
    os.environ["TQDM_DISABLE"] = "True"
    try:
        subprocess.run(["java", "-version"], check=True, capture_output=True)
    except Exception:
        print("Błąd: Java nie jest zainstalowana.")
    return True

def download_specific_language(lang_code=None):
    """
    Zapewnia obecność obu pakietów językowych SpaCy (PL i EN), 
    ponieważ prace dyplomowe bardzo często zawierają fragmenty w obu językach.
    """
    os.environ["TQDM_DISABLE"] = "True"
    try:
        import pl_core_news_lg
        print("Pakiet pl_core_news_lg jest już zainstalowany.")
    except ImportError:
        print("Pobieranie pakietu języka polskiego SpaCy (pl_core_news_lg)...")
        spacy.cli.download("pl_core_news_lg")
        
    try:
        import en_core_web_lg
        print("Pakiet en_core_web_lg jest już zainstalowany.")
    except ImportError:
        print("Pobieranie pakietu języka angielskiego SpaCy (en_core_web_lg)...")
        spacy.cli.download("en_core_web_lg")