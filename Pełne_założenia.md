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

Skuteczność modułów oceniana jest na zbiorze testowym **10 ręcznie sprawdzonych prac** (prawda referencyjna).  
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

## 4.5 Analiza merytoryczna 
Komentarze odnośnie merytoryki (np. brak SOTA, końcowa ocena merytoryki wyrażona w %) oznaczone na pierwszej stronie pracy w celu zachowania spójności z ustaloną metryką. 

Ocena merytoryczna z użyciem lokalnego LLM obejmuje wyznaczenie celu pracy, analizę tematyki rozdziałów oraz weryfikację wystąpienia i spójności sekcji SOTA z celem pracy. Ocena dotyczy kompletności i zgodności z celem pracy.

- Ekstrakcja celu pracy.
- Generowanie tematyki dla poszczególnego nagłówka.
- Generowanie słów kluczowych oraz sprawdzenie liczby ich wystąpień.
- Detekcja często powtarzających się słów oraz ocena podobieństwa do celu pracy.
- Reguła 1: wykrywanie fragmentów odnośnie SOTA na podstawie nagłówków oraz fraz typu „przegląd literatury/stan wiedzy/related work”.
- Reguła 2: weryfikacja wystąpienia SOTA poprzez zliczenie cytowań w sekcji oraz wykrycie słów kluczowych wskazujących na przegląd literatury.
- Reguła 3: weryfikacja struktury SOTA poprzez obecność podrozdziałów opisujących metody/rozwiązania w obrębie sekcji SOTA. SOTA wygląda poprawnie, jeśli są co najmniej 2 podrozdziały-metody w spisie treści oraz pracy.

### Metryka punktowa dla modułu merytoryki 

Ocena modułu merytorycznego wyrażana jest w procentach jako ważona suma trzech składowych:
- zgodność streszczeń z celem pracy – 60%,
- wystąpienie SOTA – 20%,
- słowa kluczowe / powtarzalność słów (na temat / nie na temat) – 20%.

Wynik końcowy:

$$
Score = 100 \cdot \big(0.60\cdot S_{\text{goal}} + 0.20\cdot S_{\text{sota}} + 0.20\cdot S_{\text{kw}}\big)
$$

W definicjach poniżej używane jest:

$$
I(\text{warunek})=
\begin{cases}
1, & \text{gdy warunek jest spełniony} \\
0, & \text{w przeciwnym razie}
\end{cases}
$$

## 1) Składowa SOTA (20%)

O obecności SOTA świadczą reguły z opisu modułu merytoryki:
- Reguła 1: wykrycie SOTA na podstawie nagłówków i fraz.
- Reguła 2: potwierdzenie SOTA na podstawie cytowań i słów kluczowych.
- Reguła 3: struktura SOTA (co najmniej 2 podrozdziały-metody w spisie treści oraz pracy).

Wyniki reguł:

$$
r_1 = I(\text{Reguła 1 spełniona})
$$

$$
r_2 = I(\text{Reguła 2 spełniona})
$$

$$
r_3 = I(\text{Reguła 3 spełniona})
$$

Poziom pewności wystąpienia SOTA:

$$
P_{\text{sota}} = \frac{r_1 + r_2 + r_3}{3}
$$

Składowa używana w metryce:

$$
S_{\text{sota}} = P_{\text{sota}}
$$

SOTA jest uwzględniane w wyniku zawsze jako wartość ciągła w przedziale 0..1, a nie jako warunek zaliczenia.

## 2) Zgodność streszczeń z celem pracy (60%)

LLM generuje streszczenia rozdziałów, a następnie porównuje je do wyekstraktowanego celu pracy korzystając z cosine similarity $G_{\text{llm}}$.  
Podobieństwo refernecyjne celu do treści $G$ wyznacza człowiek. Zgodność obydwu celi liczona jest jako cosine similarity w relacji: cel pracy wyznaczony przez LLM oraz przez człowieka.

$$
S_{\text{goal}} = sim(G, G_{\text{llm}})
$$

## 3) Słowa kluczowe i powtarzalność (20%)

Na podstawie słów kluczowych oraz często powtarzających się słów wyznaczana jest zgodność treści z celem pracy (na temat / nie na temat).  
Ocena referencyjna człowieka ma postać binarną: 1 = na temat, 0 = nie na temat.  
Wynik systemu również ma postać binarną.

$$
S_{\text{kw}} = I(Topic\_hat = Topic)
$$

Progi decyzyjne dla LLM są dobierane empirycznie na zbiorze testowym i zależą od zastosowanego modelu embeddingów.  
Wymagana skuteczność: Score\_avg >= 70% na zbiorze testowym (N prac).

---

## 4.6 Analiza bibliografii
- Analiza spójności zapisu (jednolita forma imion i nazwisk).
- Generowanie oraz sortowanie podsumowania bibliografii wg kryterium.

**Kryteria skuteczności:**  
F1 ≥ 0.80 oraz Precision ≥ 0.85.

---

## 4.7 Moduł plagiatu (zgodny z harmonogramem)
Sprawdzanie plagiatu realizowane jest wyłącznie poprzez otwarcie w przeglądarce wyników wyszukiwania internetowego dla fragmentu wskazanego przez użytkownika (maksymalnie 1000 znaków).

---

# 5. Wymagania sprzętowe
- Tryb pełny: rekomendowane 8 GB VRAM dla modułów LLM/vision; pozostałe moduły działają na CPU.
