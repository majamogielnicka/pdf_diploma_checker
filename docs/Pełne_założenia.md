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
- **Tryb pełny:** szacowany czas dla pracy **40–60 stron** ≤ **40 minut**.

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
- **Czułość (Recall):** TP / (TP + FN) — jak często wykryty błąd jest błędem rzeczywistym.
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

Komentarze dotyczące merytoryki (np. brak SOTA, niska zgodność z celem, końcowa ocena merytoryczna wyrażona w %) umieszczane są na pierwszej stronie pracy w celu zachowania spójności raportu.

Ocena merytoryczna z użyciem lokalnego LLM obejmuje:
- ekstrakcję celu pracy z początku dokumentu,
- generowanie streszczeń dla podrozdziałów,
- ocenę zgodności treści rozdziałów z celem pracy,
- bezpośrednią ocenę realizacji celu pracy,
- weryfikację jakości sekcji SOTA.

### Założenia modułu oceny merytorycznej

#### 1. Cel modułu

Moduł ocenia, czy praca realizuje swój cel oraz czy zawiera poprawnie opracowaną sekcję SOTA.

Ocena końcowa opiera się na trzech składowych:
- zgodności treści rozdziałów z celem pracy,
- bezpośredniej ocenie realizacji celu pracy,
- jakości sekcji SOTA.

---

#### 2. Zgodność treści z celem pracy

Dla każdego streszczenia podrozdziału wyznaczane jest podobieństwo semantyczne między **celem pracy** a **treścią podrozdziału** z użyciem embeddingów i podobieństwa cosinusowego.

Dla $i$-tego podrozdziału:

$$
s_i = \cos(\mathrm{emb}(G), \mathrm{emb}(T_i))
$$

gdzie:
- $G$ — cel pracy,
- $T_i$ — streszczenie podrozdziału,
- $s_i$ — podobieństwo podrozdziału do celu.

Następnie sprawdzane jest, które podrozdziały **nie przekraczają ustalonego progu** $\tau$.

Jeżeli:
- $N$ — liczba wszystkich podrozdziałów,
- $K$ — liczba podrozdziałów, dla których $s_i < \tau$,

to udział podrozdziałów słabo związanych z celem wynosi:

$$
P_{\mathrm{off}} = \frac{K}{N} \cdot 100
$$

Na tej podstawie wynik zgodności treści liczony jest jako:

$$
S_{\mathrm{emb}} = 100 - P_{\mathrm{off}}
$$

gdzie:
- $S_{\mathrm{emb}}$ — wynik zgodności treści z celem pracy w skali `0–100`,
- $\tau$ — próg podobieństwa, np. `0.45`.

Interpretacja:
- im więcej podrozdziałów poniżej progu, tym niższy wynik,
- jeśli wszystkie podrozdziały przekraczają próg, to $S_{\mathrm{emb}} = 100$.

---

#### 3. Ocena realizacji celu pracy

Dodatkowo model otrzymuje **cel pracy wyekstraktowany z początku dokumentu** i ocenia bezpośrednio, czy został on zrealizowany w treści całej pracy.

Wynik tej oceny oznaczany jest jako:

$$
S_{\mathrm{pr}} \in \{0, 50, 100\}
$$

gdzie:
- `100` — cel został zrealizowany,
- `50` — cel został zrealizowany częściowo,
- `0` — cel nie został zrealizowany.

Składowa ta ma charakter ekspercki i stanowi dodatkową ocenę całości pracy, niezależną od analizy podobieństw embeddingowych.

---

#### 4. Ocena sekcji SOTA

Sekcja SOTA oceniana jest na podstawie trzech reguł:
- $r_1$ — zawiera ocenę istniejących rozwiązań,
- $r_2$ — wskazuje lukę badawczą lub problem,
- $r_3$ — zawiera syntezę lub porównanie metod i podejść.

Każda reguła przyjmuje wartość:
- `1` — spełniona,
- `0` — niespełniona.

Wynik SOTA:

$$
S_{\mathrm{sota}} =
\begin{cases}
100 & \text{gdy } r_1+r_2+r_3 \ge 2 \\
50 & \text{gdy } r_1+r_2+r_3 = 1 \\
0 & \text{gdy } r_1+r_2+r_3 = 0
\end{cases}
$$

Interpretacja:
- `2 z 3` lub `3 z 3` reguł — pełna realizacja SOTA,
- `1 z 3` — częściowa realizacja,
- `0 z 3` — brak poprawnej sekcji SOTA.

---

#### 5. Wynik końcowy modułu merytorycznego

Końcowa ocena liczona jest jako:

$$
\mathrm{Score} = 0.60 \cdot S_{\mathrm{emb}} + 0.20 \cdot S_{\mathrm{pr}} + 0.20 \cdot S_{\mathrm{sota}}
$$

gdzie:
- $S_{\mathrm{emb}}$ — zgodność treści rozdziałów z celem pracy,
- $S_{\mathrm{pr}}$ — bezpośrednia ocena realizacji celu pracy,
- $S_{\mathrm{sota}}$ — jakość sekcji SOTA.

Wynik końcowy mieści się w przedziale `0–100`.

---

#### 6. Uwagi

1. Główną składową oceny jest $S_{\mathrm{emb}}$.
2. $S_{\mathrm{emb}}$ zależy od odsetka podrozdziałów, które nie przekraczają progu podobieństwa.
3. $S_{\mathrm{pr}}$ jest niezależną oceną tego, czy cel pracy został rzeczywiście zrealizowany.
4. Wartość progu $\tau$ dobierana jest empirycznie dla użytego modelu embeddingów.

**Kryteria skuteczności:**  
Średni wynik oceny merytorycznej na zbiorze testowym powinien osiągać poziom co najmniej **70%**.

---

## 4.6 Analiza bibliografii
- Analiza spójności zapisu (jednolita forma imion i nazwisk).
- Generowanie oraz sortowanie podsumowania bibliografii wg kryterium.

**Kryteria skuteczności:**  
F1 ≥ 0.80 oraz Precision ≥ 0.85.

---

## 4.7 Moduł plagiatu (zgodny z harmonogramem)

Sprawdzanie plagiatu realizowane jest wyłącznie poprzez otwarcie w przeglądarce wyników wyszukiwania internetowego dla fragmentu wskazanego przez użytkownika (maksymalnie 300 znaków).