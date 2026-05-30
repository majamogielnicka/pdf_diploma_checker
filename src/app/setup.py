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

def download_specific_language(lang_code):
    """
    Pobiera pakiet językowy SpaCy dedykowany dla wybranego języka analizy.
    Wywoływane dynamicznie po kliknięciu przycisku 'Analizuj'.
    """
    os.environ["TQDM_DISABLE"] = "True"
    if lang_code == "pl":
        try:
            import pl_core_news_lg
            print("Pakiet pl_core_news_lg jest już zainstalowany.")
        except ImportError:
            print("Pobieranie pakietu języka polskiego SpaCy...")
            spacy.cli.download("pl_core_news_lg")
    elif lang_code == "en":
        try:
            import en_core_web_lg
            print("Pakiet en_core_web_lg jest już zainstalowany.")
        except ImportError:
            print("Pobieranie pakietu języka angielskiego SpaCy...")
            spacy.cli.download("en_core_web_lg")