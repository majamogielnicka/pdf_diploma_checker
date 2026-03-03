# Stack technologiczny (całość projektu)

---

## 1) Layout / Parser PDF

- **Język:** Python 3.11+
- **PyMuPDF (fitz)** – ekstrakcja tekstu, pobieranie bounding boxów, odczyt rozmiaru i nazwy czcionki, wykrywanie obrazów, odczyt wymiarów strony, numeracja stron, pozycje bloków tekstu; szybkie przetwarzanie PDF.
- **pdfplumber** – alternatywa dla PyMuPDF; wolniejsze, ale przydatne do ekstrakcji tabel oraz analizy bardziej złożonych layoutów.
- **NumPy** – obliczenia pomocnicze (odległości, progi, równania/heurystyki).
- **regex / re** – reguły tekstowe: numeracja stron, podpisy rysunków/tabel, elementy struktury bibliografii, wzorce odwołań.
- **PyYAML** – wczytywanie i obsługa konfiguracji reguł/wytycznych w formacie YAML.
- **JSON** – format danych raportowych / alternatywa dla YAML w części konfiguracji (jeżeli wymagane).
- **matplotlib** – debug wizualny (np. rysowanie bboxów, wizualizacja marginesów).
- **pydantic** – walidacja struktur danych (DTO) między modułami.
- **pytest** – testy jednostkowe i szybkie testy regresji.

---

## 2) GUI i Plagiat

- **Język:** Python 3.11+
- **PySide6** – implementacja GUI (desktop).
- **ScraperAPI** – zewnętrzne API do pobierania treści stron (jeśli dopuszczone w projekcie); w przeciwnym razie użycie trybu „otwarcia wyszukiwarki w przeglądarce” bez scrapowania.
- **requests** – połączenia HTTP (jeśli wykorzystywane jest pobieranie treści stron).
- **BeautifulSoup4** – czyszczenie HTML i ekstrakcja tekstu ze stron.
- **RapidFuzz** – dopasowanie tekstów (odległość Levenshteina / podobieństwo) przy porównaniach fragmentów.
- **PyMuPDF (fitz)** – parser PDF (wyciąganie tekstu/fragmentów na potrzeby plagiatu).
- **PyYAML** – wczytywanie konfiguracji (np. limity, tryb szybki/dokładny).
- **JSON** – raportowanie wyników plagiatu (np. link wyszukiwarki + metadane).

---

## 3) Lingwistyka (język, redakcja, bibliografia)

- **Język:** Python 3.11+
- **JSON** – raporty/format wymiany danych.
- **Java 17+** – wymagana do działania `language_tool_python`.
- **language_tool_python** – sprawdzanie gramatyki i interpunkcji.
- **lingua-language-detector** – wykrywanie języka (PL/EN) oraz wykrywanie słów angielskich w polskim tekście.
- **regex / re** – reguły redakcyjne (np. podwójne spacje, symbole dziesiętne, wzorce bibliografii wg PN-ISO 690:2012).
- **FlashText** – szybkie wyszukiwanie fraz (np. definicja skrótu przy pierwszym użyciu).
- **thefuzz** – dopasowania tekstowe (np. dopasowanie cytowań do bibliografii, wstępna ocena spójności).
- **spaCy** – analiza składniowa zdań (heurystyki: podmiot/orzeczenie, strona bierna).
- **pandas** – analiza i podsumowania bibliografii (statystyki, spójność pól).

---

## 4) LLM + Vision (merytoryka + analiza obrazów/wykresów)

- **Język:** Python 3.11+
- **Ollama** – uruchamianie lokalnego modelu LLM.
- **Modele LLM:**
  - **bielik** – język polski
  - **qwen2.5** – język angielski
- **sentence-transformers** – embeddingi do oceny podobieństwa semantycznego (np. zgodność SOTA z celem pracy, zgodność sekcji z tematyką).
- **torch** – backend dla modeli (wymagany przez modele embeddingowe; CPU lub GPU).
- **pydantic** – walidacja struktur wyników merytorycznych (np. checklisty: teoria/SOTA/metodologia/cel).
- **NumPy** – obliczenia pomocnicze (progi podobieństwa, metryki).
- **OpenCV** – analiza obrazów (kontrast, ostrość, heurystyki dla wykresów).
- **Pillow (PIL)** – podstawowa obróbka obrazów (konwersje, przycięcia, formaty).
- **matplotlib** – debug wizualny (podgląd wykrytych obszarów, bboxów, osi wykresów).
- **scikit-image** – dodatkowe metryki jakości obrazu/cech.
- **pytest** – testy jednostkowe (walidacja detekcji sekcji i metryk wizualnych).

---

## 5) Wspólne konwencje danych i raportów

- **JSON** – konfiguracja reguł (wytyczne uczelni).
- **JSON/CSV** – raporty wyników (lista błędów, metadane).
