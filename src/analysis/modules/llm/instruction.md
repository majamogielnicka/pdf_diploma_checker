# Moduł LLM

Moduł `llm` odpowiada za analizę merytoryczną pracy dyplomowej z użyciem lokalnego modelu językowego GGUF oraz modeli embeddingowych.
Model ocenia w jakim stopniu praca jest na temat oraz analizuje sekcję z aktualnym stanem wiedzy zgodnie z plikiem założenia.md znajdującym się w katalogu "docs"

Projekt nie korzysta już z Ollamy. Model LLM uruchamiany jest lokalnie przez `llama-cpp-python`.

---

## Wymagania

Przed uruchomieniem modułu zainstaluj zależności projektu oraz zapoznaj się z plikiem, aby poprawnie pobrać model lokalnie

```bash
pip install -r requirements.txt