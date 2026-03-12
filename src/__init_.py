"""
# 🛡️ System LLM & VISION - Dokumentacja Projektu

Ten pakiet stanowi kompleksowe rozwiązanie do procesowania prac dyplomowych i raportów medycznych.
Został zaprojektowany w architekturze **UV Lock**, co gwarantuje wysoką jakość danych wejściowych
dla modeli językowych.

## 🧱 Struktura Modułów
* **`parse_raport`**: Odpowiada za czyszczenie surowych plików tekstowych z szumu, 
    kodu i artefaktów składu.
* **`get_summary`**: Moduł generujący zwięzłe streszczenia przy użyciu modelu **Bielik**.
* **`get_purpose`**: Narzędzie do głębokiej analizy intencji autora tekstu.

## ⚙️ Wymagania Techniczne
1. **Ollama**: Musi być uruchomiona lokalnie (`http://localhost:11434`).
2. **Model**: Wymagany model `SpeakLeash/bielik-7b-instruct-v0.1-gguf:latest`.
3. **Środowisko**: Python 3.12+ z zainstalowanymi paczkami z `requirements.txt`.

---
© 2026 Grupa LLM & VISION | *Dokumentacja generowana automatycznie.*
"""