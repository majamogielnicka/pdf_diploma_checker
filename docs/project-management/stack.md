# Stack technologiczny

---

## 1) Layout / Parser PDF

- **PyMuPDF (fitz)** – główny silnik ekstrakcji.
- **statistics** – analiza heurystycznea: ocena justowania tekstu (odchylenie standardowe), precyzyjne wykrywanie spacji/wcięć (mediana przerw) oraz obliczanie dominującej interlinii w dokumencie.
- **dataclasses** – wykorzystywane do tworzenia struktur dokumentu (np. bloki tekstu, listy, nagłówki, elementy wizualne) oraz ich łatwego parsowania do formatu JSON.
- **pathlib** / **os** – obsługa ścieżek.
- **regex / re** – reguły tekstowe i klasyfikacja: wykrywanie numeracji stron, identyfikacja wzorców list (kropki, nawiasy, myślniki), akronimów oraz podpisów tabel i rysunków.
- **typing** - adnotacje typów (`Dict`, `Any`, `List`)
---

## 2) GUI i Plagiat

- **PySide6** – implementacja GUI.
- **BeautifulSoup4** – czyszczenie HTML i ekstrakcja tekstu ze stron.
- **PyMuPDF (fitz)** – parser PDF (wyciąganie tekstu/fragmentów na potrzeby plagiatu).
- **webbrowser** – otwieranie stron internetowych w przeglądarce.
- **urllib.parse** - analiza oraz budowa adresów URL.

Opcjonalnie: 
- **ScraperAPI** – zewnętrzne API.
- **requests** – połączenia HTTP.
- **RapidFuzz** – dopasowanie tekstów (odległość Levenshteina / podobieństwo) przy porównaniach fragmentów.

---

## 3) Lingwistyka (język, redakcja, bibliografia)

- **Java 17+** – wymagana do działania `language_tool_python`.
- **spaCy** – analiza składniowa zdań, wykorzystywane modele: `en_core_web_lg` (angielski) i `pl_core_news_lg` (polski)
- **language_tool_python** – sprawdzanie gramatyki, pisowni i interpunkcji w języku polskim i angielskim
- **lingua** – wykrywanie języka bloku tekstu (PL/EN) oraz identyfikacja słów angielskich w polskim tekście
- **morfeusz2** – morfologiczna analiza języka polskiego, weryfikacja form osobowych czasowników
- **re** – wyrażenia regularne do wykrywania błędów redakcyjnych
- **dataclasses** – definicje typów danych
- **typing** – adnotacje typów (`Union`)
- **collections** – `defaultdict` do grupowania błędów według bloków i lemmatów
- **string** – operacje na znakach
- **functools** – `cache` do cachowania wyników lemmatyzacji

---

## 4) LLM + Vision (merytoryka + analiza obrazów/wykresów)

- **PyMuPDF** (`fitz`) – ekstrakcja tekstu i metadanych z plików PDF (rozmiary fontów, bloki tekstu, wykrywanie nagłówków)
- **llama_cpp** – uruchamianie lokalnych modeli LLM w formacie GGUF (analiza SOTA, ekstrakcja celu pracy, generowanie streszczeń)
- **huggingface_hub** – pobieranie modeli językowych z Hugging Face Hub
- **sentence_transformers** – generowanie embeddingów tekstowych do obliczania podobieństwa cosinusowego
- **scikit-learn** (`sklearn`) – obliczanie podobieństwa cosinusowego między embeddingami
- **requests** – obsługa błędów połączenia z modelami
- **re** – wyrażenia regularne do wykrywania cytowań, nagłówków, wzorców bibliograficznych
- **dataclasses** – definicje typów danych (`ChapterBlock`, `SubtitleBlock`)
- **collections** – zliczanie rozmiarów fontów (`Counter`)
- **datetime** – znaczniki czasu w plikach wynikowych
- **importlib** – dynamiczny import modułów w runtime
- **traceback** – szczegółowe komunikaty błędów
- **time** – mierzenie czasu przetwarzania plików
- **typing** – adnotacje typów (`Dict`, `Any`, `List`)

---

## 5) Spis ogólny

- **Język:** Python 3.11+.
- **JSON** – konfiguracja reguł (wytyczne uczelni), raporty wyników (lista błędów, metadane).
- **os** / **sys** – zarządzanie strukturą katalogów, operacje na plikach (czyszczenie i zapis obrazów) oraz ręczne zarządzanie ścieżkami importów (`sys.path`) pomiędzy modułami aplikacji.
- **logging** –  zarządzanie logami i przechwytywanie błędów z modułów (zamiast standardowego wyjścia konsoli). 
