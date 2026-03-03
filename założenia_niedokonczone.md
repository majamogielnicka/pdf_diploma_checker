# Założenia projektowe

## 1. Cel, forma działania i czas wykonania

Opracowanie lokalnego systemu analizy pracy dyplomowej w formacie PDF wraz z generowaniem pliku PDF z naniesionymi komentarzami wskazującymi kategorie błędów (**bez modyfikacji treści źródłowej**).

### Forma działania
- Uruchomienie jako aplikacja desktopowa (GUI) na **Windows 10/11** oraz **Linux**.
- Poprawne działanie dla PDF wygenerowanych z:
  - **MS Word Online / Office 365**,
  - **MS Word 2019+**,
  - **LaTeX2e/LaTeX3** (pdfLaTeX / XeLaTeX / LuaLaTeX).

### Czas wykonania
- **Tryb szybki:** analiza w czasie ≤ **5 minut**.
- **Tryb pełny:** szacowany czas dla pracy **40–60 stron**:
  - **15–40 min (CPU)** lub
  - **8–20 min (GPU 8 GB VRAM)**.

### Zakres trybu szybkiego
Tryb szybki obejmuje:
- analizę językową (gramatyka, ortografia, interpunkcja, struktura zdań, strona bierna),
- analizę redakcyjną podstawową,
- analizę redakcyjną rozszerzoną,
- analizę bibliografii,
- moduł plagiatu (sprawdzenie zaznaczonego fragmentu w wyszukiwarce).

### Zakres trybu pełnego
Tryb pełny obejmuje:
- wszystkie elementy trybu szybkiego,
- analizę merytoryczną (LLM lokalny): wystąpienie elementów takich jak **SOTAteoria**, **SOTA**, **metodologia**, **koncepcja**, **testy**, **cel** oraz **potwierdzenie celu**,
- analizę wizualną wykresów.

---

## 2. Wejście i wyjście

### 2.1 Wejście
- 1 plik PDF pracy dyplomowej,
- plik konfiguracyjny reguł w formacie **JSON**,
- wybór języka analizy: **PL** lub **EN**.

### 2.2 Wyjście
- plik PDF z naniesionymi komentarzami dla wykrytych błędów.

---

## 3. Metryka pomiaru skuteczności działania

Skuteczność modułów oceniana jest na zbiorze testowym **20 ręcznie sprawdzonych prac** (prawda referencyjna).  
Dla każdej kategorii liczone są **TP/FP/FN/TN** oraz metryki: **Precision**, **Recall**, **F1** oraz **Accuracy**.

### Definicje metryk
- **Precision** = TP / (TP + FP)
- **Recall** = TP / (TP + FN)
- **F1** = 2 · (Precision · Recall) / (Precision + Recall)
- **Accuracy** = (TP + TN) / (TP + TN + FP + FN)

### Interpretacja
- **Precyzja (Precision):** TP / (TP + FP) — jak często program poprawnie wykrywa błąd.
- **Czułość (Recall):** TP / (TP + FN) — ile rzeczywistych błędów wykrył program.
- **F1:** 2 · (Precyzja · Czułość) / (Precyzja + Czułość) — kompromis między precyzją i czułością.
- **Dokładność (Accuracy):** (TP + TN) / (TP + TN + FP + FN) — ogólna poprawność klasyfikacji.

### Zestaw testowy
Zestaw testowy będzie składał się z **10 ręcznie sprawdzonych prac**.
