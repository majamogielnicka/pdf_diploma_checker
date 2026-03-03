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

# 4. Zakres funkcjonalny

## 4.1 Lingwistyka (PL/EN)
- Wykrywanie błędów: gramatyka, ortografia, interpunkcja.
- Analiza struktury zdań: wykrywanie braku podmiotu/orzeczenia.
- Detekcja strony biernej.

**Kryteria skuteczności:**  
F1 ≥ 0.85 oraz Precision ≥ 0.80. Maksymalnie 1 fałszywy błąd na stronę tekstu.

---

## 4.2 Redakcja podstawowa (wymagania z konfiguracji JSON, w tym wytyczne PG)
- Liczba stron tekstu: inż. 40–50, mgr 60–80.
- Format i układ: A4, pionowa, 10 pt, interlinia 1.5, justowanie, marginesy lustrzane, numeracja w stopce (bez strony tytułowej), brak pustych stron.
- Elementy: podpis tabeli nad tabelą, podpis rysunku pod rysunkiem, przywołania tabel/rysunków/cytatów w tekście, definicja terminu/skrótu przy pierwszym użyciu.
- Bibliografia względem PN-ISO 690:2012 w zakresie reguł z konfiguracji.

**Kryteria skuteczności:**  
F1 ≥ 0.90 oraz Precision ≥ 0.85.

---

## 4.3 Redakcja rozszerzona
- Wykrywanie: szewce, bękarty, sierotki, wdowy, korytarze (w zakresie możliwym na podstawie layoutu PDF).
- Spójność symboli dziesiętnych i odnośników do rysunków/tabel.
- Rozpoczynanie rozdziałów od nowej strony.
- Podwójne spacje.
- Łączniki i myślniki.
- Cudzysłowy.
- Spójność interpunkcji w listach.
- Cytaty.
- Inne błędy edycyjne zdefiniowane w konfiguracji JSON.

**Kryteria skuteczności:**  
F1 ≥ 0.85 oraz Recall ≥ 0.80.

---

## 4.4 Analiza wizualna
- Ocena czytelności/jakości grafik oraz rozróżnienie grafiki rastrowej i wektorowej.
- Weryfikacja obecności podpisów osi i jednostek na wykresach.
- Weryfikacja spójności rozmiaru czcionki na wykresach.
- Weryfikacja obecności podpisów/źródeł przy rysunkach jako kontrola formalna.

**Kryteria skuteczności:**  
F1 ≥ 0.75 oraz Precision ≥ 0.80.

---

## 4.5 Analiza merytoryczna (LLM lokalny)
Ocena merytoryczna z użyciem lokalnego LLM obejmuje wyznaczenie celu pracy, analizę tematyki rozdziałów oraz weryfikację wystąpienia i spójności sekcji SOTA z celem pracy. Ocena dotyczy kompletności i zgodności z celem pracy.

- Ekstrakcja celu pracy.
- Generowanie tematyki dla poszczególnego nagłówka.
- Generowanie słów kluczowych oraz sprawdzenie liczby ich wystąpień.
- Detekcja często powtarzających się słów oraz ocena podobieństwa do celu pracy.
- Reguła 1: wykrywanie fragmentów odnośnie SOTA na podstawie nagłówków oraz fraz typu „przegląd literatury/stan wiedzy/related work”.
- Reguła 2: weryfikacja wystąpienia SOTA poprzez zliczenie cytowań w sekcji oraz wykrycie słów kluczowych wskazujących na przegląd literatury.
- Reguła 3: weryfikacja struktury SOTA poprzez obecność podrozdziałów opisujących metody/rozwiązania w obrębie sekcji SOTA. SOTA wygląda poprawnie, jeśli są co najmniej 2 podrozdziały-metody w spisie treści oraz pracy.

### Metryka punktowa dla modułu merytoryki (LLM)

Ocena modułu merytorycznego wykonywana jest punktowo, a następnie przeliczana na procent maksymalnej liczby punktów. Cel pracy ma większą wagę niż SOTA.

**1) Cel pracy (3 pkt)**  
LLM generuje streszczenia rozdziałów, a następnie na ich podstawie wyznacza cel pracy \(\hat{G}\). Cel referencyjny \(G\) wyznacza człowiek. Liczone jest podobieństwo semantyczne \(sim(G,\hat{G})\).

$$
P_{\text{goal}} = 3 \cdot \mathbb{1}\big(sim(G,\hat{G}) \ge T_G\big)
$$

**2) SOTA (łącznie 3 pkt)**  
SOTA oceniane jest trzema regułami (po 1 pkt każda), porównywanymi z oceną człowieka.

$$
P_{\text{sota}} = \sum_{j=1}^{3} 1 \cdot \mathbb{1}(\hat{y}_j = y_j)
$$

**3) Wynik końcowy**  

$$
S = P_{\text{goal}} + P_{\text{sota}}
$$

$$
W = 6
$$

$$
Score = \frac{S}{W}\cdot 100\%
$$

$$
Score_{\text{avg}}=\frac{1}{N}\sum_{i=1}^{N}Score_i
$$

---

## 4.6 Analiza bibliografii
- Analiza spójności zapisu (jednolita forma imion i nazwisk).
- Generowanie oraz sortowanie podsumowania bibliografii wg kryterium.

**Kryteria skuteczności:**  
F1 ≥ 0.80 oraz Precision ≥ 0.85.

---

## 4.7 Moduł plagiatu (zgodny z harmonogramem)
Sprawdzanie plagiatu realizowane jest wyłącznie poprzez otwarcie w przeglądarce wyników wyszukiwania internetowego dla fragmentu wskazanego przez użytkownika.

---

# 5. Wymagania sprzętowe
- Tryb pełny: rekomendowane 8 GB VRAM dla modułów LLM/vision; pozostałe moduły działają na CPU.
