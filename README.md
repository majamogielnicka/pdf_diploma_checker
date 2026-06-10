<div align="center">

# pdf_diploma_checker

**Automatyczna kontrola jakości prac dyplomowych w PDF – typografia, lingwistyka i merytoryka.**  

**[English below](#english)**

</div>

---

## Czym jest to narzędzie?

**pdf_diploma_checker** przyjmuje pracę w formacie PDF wygenerowane z:
MS Word Online / Office 365,
MS Word 2019+,
LaTeX2e/LaTeX3 (pdfLaTeX / XeLaTeX / LuaLaTeX) i przeprowadza serię automatycznych kontroli – od interlinii i marginesów, przez gramatykę i składnię zdań, po spójność bibliografii względem normy PN-ISO 690 – a następnie zwraca pracę PDF z naniesionymi komentarzami oraz raport merytoryczny.

Narzędzie działa w dwóch trybach:

| Tryb | Zakres |
|---|---|
| **Tryb szybki** | Kontrole formalne, typograficzne, językowe i bibliograficzne (pełna lista poniżej) |
| **Tryb szczegółowy** | Dodatkowo ocena merytoryczna z użyciem modelu (skala 0–100) oraz pogłębiona analiza grafik |

---

## Funkcje

### Tryb szybki

#### Sprawdzanie względem pliku konfiguracyjnego

- weryfikacja poprawności rozmiaru interlinii,
- sprawdzanie liczby stron,
- weryfikacja poprawności wielkości czcionki,
- sprawdzanie poprawności formatu marginesów (marginesy lustrzane),
- weryfikacja poprawności formatu oraz ułożenia strony,
- weryfikacja poprawności czcionek,
- sprawdzanie justowania.

#### Sprawdzanie ogólne

- sprawdzanie obecności pustych stron,
- weryfikacja poprawności numeracji stron,
- weryfikacja obecności spisu treści / tabel / rysunków oraz poprawnej, niemalejącej numeracji,
- weryfikacja zgodności rozdziałów / tabel / rysunków ze spisem treści / tabel / rysunków,
- weryfikacja grafik pod względem rozdzielczości, spójności czcionki na grafikach oraz oznaczenia grafik rastrowych,
- sprawdzanie, czy akronimy pojawiające się w tekście występują w spisie skrótów bądź akronimów,
- wykrywanie błędów typograficznych: sierot, wdów, szewców oraz bękartów,
- weryfikacja poprawności odnośników bibliograficznych,
- tworzenie podsumowania bibliografii.

#### Interpunkcja

- sprawdzanie poprawności użycia przecinków – wykrywanie przecinków zbędnych oraz brakujących,
- weryfikacja poprawności użycia dywizów, półpauz oraz pauz,
- weryfikacja poprawnych zakończeń i spójności w zapisie list.

#### Gramatyka

- znajdowanie literówek w tekście,
- znajdowanie niezdefiniowanych nazw własnych oraz akronimów.

#### Styl

- wskazywanie błędów stylistycznych.

#### Składnia zdań w paragrafach

- wykrywanie użycia pierwszej osoby w tekście,
- podsumowanie stosunku zdań czynnych, biernych oraz równoważników zdania,
- wykrywanie zdań niezawierających podmiotu i/lub orzeczenia.

#### Separatory dziesiętne

- weryfikacja użycia poprawnych separatorów dziesiętnych.

#### Skróty

- weryfikacja, czy skróty używane w pracy posiadają definicję przy pierwszym użyciu.

#### Bibliografia

- weryfikacja spójności zapisu bibliografii pod kątem formatu autorów, dat, tytułów i separatorów,
- weryfikacja spójnej kolejności wpisów w całej bibliografii,
- weryfikacja, czy wpis bibliograficzny został zakończony kropką,
- wykrywanie brakujących danych we wpisie bibliograficznym,
- weryfikacja typu wpisu,
- dodatkowa weryfikacja pól dla formatu BibTeX.

### Tryb szczegółowy

#### Analiza merytoryczna

Moduł merytoryki zwraca ocenę ogólną w skali **0–100**, tworzoną na podstawie ważonych ocen cząstkowych:

- realizacji celu pracy przez autora,
- spójności podnagłówków z celem pracy,
- poprawności przeglądu stanu wiedzy.

#### Analiza grafik (opcjonalna, z poziomu GUI)

GUI umożliwia opcjonalną dokładną analizę grafik z użyciem modelu oraz wygenerowanie raportu końcowego z ocenami grafik i ogólną analizą merytoryczną. Analiza obejmuje:

- detekcję spójności rozmiaru czcionki na wykresach,
- weryfikację czytelności obrazków,
- sprawdzanie, czy dane przywoływane w tekście pokrywają się z danymi na obrazkach,
- sprawdzanie, czy autor odwołuje się w pracy do użytych obrazków.

---

### Kilka pojęć użytych powyżej, które mogą być nieznane:

### Błędy typograficzne

| Termin (PL) | Termin (EN) | Znaczenie |
|---|---|---|
| **Sierota** | *hanging conjunction* | Jednoliterowy spójnik lub przyimek (a, i, o, u, w, z) pozostawiony na końcu wiersza zamiast przeniesienia go do następnego. |
| **Wdowa** | *runt* | Bardzo krótki ostatni wiersz akapitu – np. pojedyncze słowo lub sylaba – pozostawiający nieestetyczną, niemal pustą linię. |
| **Szewc** | *orphan* | Pierwszy wiersz akapitu pozostawiony samotnie na dole strony lub łamu, podczas gdy reszta akapitu znajduje się na następnej stronie. |
| **Bękart** | *widow* | Ostatni wiersz akapitu przeniesiony samotnie na górę następnej strony lub łamu. |

Wszystkie cztery psują estetykę strony i utrudniają czytanie – dlatego zasady składu tekstu oraz wytyczne formatowania prac dyplomowych ich zakazują.

### BibTeX

**BibTeX** to tekstowy format zapisu danych bibliograficznych, używany przede wszystkim w połączeniu z LaTeX-em. Każdy wpis ma określony typ (`@article`, `@book`, `@inproceedings`, …) oraz zestaw pól:

```bibtex
@article{kowalski2024,
  author  = {Kowalski, Jan and Nowak, Anna},
  title   = {Biodegradable scaffolds for tissue engineering},
  journal = {Acta of Bioengineering},
  year    = {2024},
  volume  = {26},
  pages   = {15--27},
  doi     = {10.1000/xyz123}
}
```

Narzędzie dodatkowo pozwala na weryfikację, czy każdy typ wpisu zawiera wymagane dla niego pola.

---

## Instalacja i konfiguracja

[Przewodnik konfiguracji](./config_guide.md)  


---

## Użycie

[Instrukcja Użytkownika](./user_guide.md)

---
<div align="center">  

<a id="english"></a>   

# pdf_diploma_checker

**Automated quality control for academic theses in PDF – typography, language and content**

</div>

---

## What is it?

**pdf_diploma_checker** takes a thesis in PDF generated from:
MS Word Online / Office 365,
MS Word 2019+,
LaTeX2e/LaTeX3 (pdfLaTeX / XeLaTeX / LuaLaTeX) and runs a battery of automated checks – from line spacing and margins, through Polish grammar and sentence syntax, to bibliography coherence against PN-ISO 690 – returns a PDF with comments and a detailed report fie.

The tool works in two modes:

| Mode | What it does |
|---|---|
| **Fast mode** | Formal, typographic, linguistic and bibliographic checks (full list below) |
| **Detailed mode** | Adds a model-based content evaluation (0–100 score) and in-depth figure analysis |

---

## Features

### Fast mode

#### Checks against a configuration file

- line spacing verification
- page count check
- font size verification
- margin format check (mirror margins)
- page format and orientation verification
- font verification
- justification check

#### General checks

- detection of blank pages,
- page numbering verification,
- presence of table of contents / list of tables / list of figures, with correct non-decreasing numbering,
- consistency of chapters / tables / figures with their respective lists,
- figure verification: resolution, font consistency within figures, raster graphics labelling,
- checking that acronyms used in the text appear in the list of abbreviations/acronyms,
- detection of typographic errors: orphans, widows, runts and hanging conjunctions,
- verification of bibliography references,
- bibliography summary generation.

#### Punctuation

- comma usage check – detection of redundant and missing commas,
- correct usage of hyphens, en dashes and em dashes,
- correct endings and consistency in list formatting.

#### Grammar

- typo detection,
- detection of undefined proper names and acronyms.

#### Style

- detection of stylistic errors

#### Sentence syntax in paragraphs

- detection of first-person verb forms,
- summary of the ratio of active sentences, passive sentences and sentence equivalents (verbless clauses),
- detection of sentences missing a subject and/or a predicate.

#### Decimal separators

- verification of correct decimal separator usage.

#### Abbreviations

- checking that abbreviations are defined at first use.

#### Bibliography

- consistency of author format, dates, titles and separators across the bibliography,
- consistent entry ordering throughout the bibliography,
- checking that each entry ends with a full stop,
- detection of missing data in entries,
- entry type verification,
- additional field verification for BibTeX entries.

### Detailed mode

#### Content evaluation

The content module returns an overall score from **0 to 100**, computed as a weighted combination of partial scores for:

- how well the author realises the stated goal of the thesis,
- coherence of subheadings with the thesis goal,
- quality of the state-of-the-art review.

#### Figure analysis (optional, via GUI)

The GUI offers an optional in-depth, model-based analysis of figures and generates a final report with figure scores and the overall content evaluation. The analysis covers:

- font size consistency on charts,
- figure legibility verification,
- checking that data referenced in the text matches the data shown in figures,
- checking that every figure used is actually referenced in the text.

---

## A few terms used above that may be unfamiliar:


### Typographic errors

| Term (EN) | Term (PL) | Meaning |
|---|---|---|
| **Orphan** | *szewc* | The **first line of a paragraph** left alone at the **bottom** of a page or column, while the rest of the paragraph continues on the next page. |
| **Widow** | *bękart* | The **last line of a paragraph** pushed alone to the **top** of the next page or column. |
| **Runt** | *wdowa* | A very short **last line of a paragraph** – e.g. a single word or syllable – leaving an unsightly, almost empty line. |
| **Hanging conjunction** | *sierota* | A single-letter conjunction or preposition (in Polish: *a, i, o, u, w, z*) left **at the end of a line** instead of being moved to the next one. Specific to Polish typographic convention. |

All four make a page look unprofessional and harm readability, which is why publishing and thesis-formatting guidelines forbid them.

### BibTeX

**BibTeX** is a plain-text format for storing bibliographic data, used primarily with LaTeX. Each entry has a type (`@article`, `@book`, `@inproceedings`, …) and a set of fields:

```bibtex
@article{kowalski2024,
  author  = {Kowalski, Jan and Nowak, Anna},
  title   = {Biodegradable scaffolds for tissue engineering},
  journal = {Acta of Bioengineering},
  year    = {2024},
  volume  = {26},
  pages   = {15--27},
  doi     = {10.1000/xyz123}
}
```

The tool additionally offers verification of that each entry type contains its required fields.


---

## Installation & setup

[Config guide](./config_guide.md)  

---

## Usage

[User guide](./user_guide.md)
