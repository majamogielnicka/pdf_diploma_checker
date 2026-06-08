# Moduł LLM

Moduł `llm` odpowiada za analizę merytoryczną pracy dyplomowej z użyciem lokalnego modelu językowego GGUF oraz modeli embeddingowych.
Model ocenia w jakim stopniu praca jest na temat oraz analizuje sekcję z aktualnym stanem wiedzy zgodnie z plikiem założenia.md znajdującym się w katalogu "docs"

Projekt nie korzysta już z Ollamy. Model LLM uruchamiany jest lokalnie przez `llama-cpp-python`.

---

## Wymagania

Przed uruchomieniem modułu zainstaluj zależności projektu oraz zapoznaj się z plikiem, aby poprawnie pobrać model lokalnie

```bash
pip install -r requirements.txt

Po instalacji zależności należy sprawdzić i w razie potrzeby zmienić konfigurację w pliku:
src/analysis/modules/llm/config.py

Zmianie podlegają trzy linijki oznaczone komentarzem: 
- MODEL_PATH - jeśli model został zainstalowany w miejscu innym niż domyślny w skrypcie download_model.py
- THESIS_PATH - ścieżka do pracy analizowanej uruchamiając ze skryptu głównego, a nie ścieżkę importowaną przez aplikację główną
- LANGUAGE - język analizowanej pracy