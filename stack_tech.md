# Stack technologiczny

---

## 1) Layout / Parser PDF

- **Język:** Python 3.11+
- **PyMuPDF (fitz)** – ekstrakcja tekstu, pobieranie bounding boxów, odczyt rozmiaru i nazwy czcionki, wykrywanie obrazów, odczyt wymiarów strony, numeracja stron, pozycje bloków tekstu; szybkie przetwarzanie PDF.
- **pdfplumber** – alternatywa dla PyMuPDF; przydatne do ekstrakcji tabel oraz analizy bardziej złożonych layoutów.
- **NumPy** – obliczenia pomocnicze.
- **regex / re** – reguły tekstowe: numeracja stron, podpisy rysunków/tabel, elementy struktury bibliografii, wzorce odwołań.
- **JSON** – format danych raportowych..
- **matplotlib** – debug wizualny (np. rysowanie bboxów, wizualizacja marginesów).
- **pydantic** – walidacja struktur danych między modułami.
- **pytest** – testy jednostkowe.

---

## 2) GUI i Plagiat

- **Język:** Python 3.11+
- **PySide6** – implementacja GUI.
- **requests** – połączenia HTTP.
- **BeautifulSoup4** – czyszczenie HTML i ekstrakcja tekstu ze stron.
- **PyMuPDF (fitz)** – parser PDF (wyciąganie tekstu/fragmentów na potrzeby plagiatu).
- **JSON** – wczytywanie konfiguracji
Opcjonalnie: 
- **ScraperAPI** – zewnętrzne API.
- **requests** – połączenia HTTP.
- **RapidFuzz** – dopasowanie tekstów (odległość Levenshteina / podobieństwo) przy porównaniach fragmentów.

---

## 3) Lingwistyka (język, redakcja, bibliografia)

- **Język:** Python 3.11+
- **JSON** 
- **Java 17+** – wymagana do działania `language_tool_python`.
- **language_tool_python** – sprawdzanie gramatyki i interpunkcji.
- **lingua-language-detector** – wykrywanie języka (PL/EN) oraz wykrywanie słów angielskich w polskim tekście.
- **regex / re** – reguły redakcyjne (np. podwójne spacje, symbole dziesiętne, wzorce bibliografii wg PN-ISO 690:2012).
- **FlashText** – szybkie wyszukiwanie fraz (np. definicja skrótu przy pierwszym użyciu).
- **thefuzz** – dopasowania tekstowe (np. dopasowanie cytowań do bibliografii, wstępna ocena spójności).
- **spaCy** – analiza składniowa zdań (heurystyki: podmiot/orzeczenie, strona bierna).
- **pandas** – analiza struktury składniowej zdań 

---

## 4) LLM + Vision (merytoryka + analiza obrazów/wykresów)

- **Język:** Python 3.11+
- **Ollama** – uruchamianie lokalnego modelu LLM.
- **Modele LLM:**
  - **bielik** – język polski
  - **qwen2.5** – język angielski
- **sentence-transformers** – embeddingi do oceny podobieństwa semantycznego (np. zgodność SOTA z celem pracy, zgodność sekcji z tematyką).
- **torch** – backend dla modeli (wymagany przez modele embeddingowe; CPU lub GPU).
- **pydantic** – walidacja struktur wyników merytorycznych.
- **NumPy** – obliczenia pomocnicze (progi podobieństwa, metryki).
- **OpenCV** – analiza obrazów (kontrast, ostrość, heurystyki dla wykresów).
- **Pillow (PIL)** – podstawowa obróbka obrazów (konwersje, przycięcia, formaty).
- **matplotlib** – debug wizualny (podgląd wykrytych obszarów, bboxów, osi wykresów).
- **scikit-image** – dodatkowe metryki jakości obrazu/cech.
- **pytest** – testy jednostkowe.

---

## 5) Wspólne konwencje danych i raportów

- **JSON** – konfiguracja reguł (wytyczne uczelni).
- **JSON/CSV** – raporty wyników (lista błędów, metadane).
