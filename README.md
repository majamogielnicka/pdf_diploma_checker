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

##### Jak liczona jest ocena?

Wynik końcowy jest sumą ważoną trzech składowych:

$$
\mathrm{Score} = 0.60 \cdot S_{\mathrm{emb}} + 0.20 \cdot S_{\mathrm{pr}} + 0.20 \cdot S_{\mathrm{sota}}
$$

**1. Zgodność treści z celem pracy ($S_{\mathrm{emb}}$)** - główna składowa oceny. Dla każdego podrozdziału generowane jest streszczenie, a następnie wyznaczane jest podobieństwo semantyczne (cosinusowe, na embeddingach) między celem pracy $G$ a streszczeniem podrozdziału $T_i$:

$$
s_i = \cos(\mathrm{emb}(G), \mathrm{emb}(T_i))
$$

Podrozdziały, których podobieństwo nie przekracza progu $\tau$, uznawane są za słabo związane z celem. Jeśli $K$ z $N$ podrozdziałów nie przekracza progu, to:

$$
S_{\mathrm{emb}} = 100 - \frac{K}{N} \cdot 100
$$

Im więcej podrozdziałów poniżej progu, tym niższy wynik; jeśli wszystkie przekraczają próg, $S_{\mathrm{emb}} = 100$.

**2. Bezpośrednia ocena realizacji celu ($S_{\mathrm{pr}}$)** – model otrzymuje cel pracy wyekstraktowany z początku dokumentu i ocenia bezpośrednio, czy został on zrealizowany w treści całej pracy: `100` – cel zrealizowany, `50` – zrealizowany częściowo, `0` – niezrealizowany.

**3. Jakość przeglądu stanu wiedzy ($S_{\mathrm{sota}}$)** – sekcja SOTA oceniana jest według trzech reguł: zawiera ocenę istniejących rozwiązań, wskazuje lukę badawczą lub problem, zawiera syntezę lub porównanie metod i podejść. Spełnienie co najmniej 2 z 3 reguł daje `100`, dokładnie 1 reguły – `50`, żadnej – `0`.


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

## Instalacja, konfiguracja i użycie

### 1. Przed uruchomieniem aplikacji

Przed rozpoczęciem analizy upewnij się, że:

1. Aplikacja została poprawnie zainstalowana lub rozpakowana.
2. Plik `app_config.json` znajduje się we właściwej lokalizacji.
3. Wymagane modele lokalne są dostępne.
4. Plik PDF, który chcesz przeanalizować, jest gotowy.
5. W aplikacji wybrano poprawny język pracy dyplomowej.

Aplikacji nie należy uruchamiać bezpośrednio z wnętrza archiwum ZIP. Najpierw rozpakuj pakiet.

### 2. Plik konfiguracyjny

Aplikacja wymaga pliku konfiguracyjnego o nazwie:

```text
app_config.json
```

Plik ten odpowiada za podstawowe ustawienia aplikacji, takie jak katalog modeli oraz tryb sprzętowy.

Przykładowe pliki:

```text
cpu_config.json
gpu_config.json
```

są jedynie szablonami. Aby skorzystać z jednego z nich, skopiuj go i zmień nazwę kopii na:

```text
app_config.json
```

Jeśli plik `app_config.json` nie istnieje lub ma inną nazwę, aplikacja może nie uruchomić się poprawnie.

### 3. Lokalizacje modeli i plików

Aplikacja korzysta z plików lokalnych przechowywanych na komputerze użytkownika.

Przed uruchomieniem analizy upewnij się, że plik konfiguracyjny wskazuje na właściwy katalog modeli oraz że wymagane pliki modeli są dostępne.

### Lokalizacja pliku konfiguracyjnego

Plik konfiguracyjny musi znajdować się w głównym katalogu aplikacji.

Przykład:

```text
pdf_diploma_checker/
├── app_config.json
├── cpu_config.json
├── gpu_config.json
├── src/
├── requirements.txt
└── README.md
```

Pliki:

```text
cpu_config.json
gpu_config.json
```

są wyłącznie szablonami. Można je skopiować i zmienić ich nazwę na:

```text
app_config.json
```

### Lokalizacja katalogu modeli

Katalog modeli jest zdefiniowany w pliku `app_config.json` w polu:

```json
"model_dir": "PATH_TO_MODELS_DIR"
```

Przykład w systemie Windows:

```json
"model_dir": "C:/Users/YOUR_USERNAME/models"
```

Przykład w systemie Linux:

```json
"model_dir": "/home/YOUR_USERNAME/models"
```

Ścieżka powinna wskazywać na główny folder zawierający wszystkie wymagane lokalne pliki modeli.

### Wymagana struktura modeli

Katalog modeli powinien mieć następującą strukturę:

```text
PATH_TO_MODELS_DIR/
├── gemma3_12b/
│   └── google_gemma-3-12b-it-Q4_K_M.gguf
├── llava-v1.6-mistral-7b.Q4_K_M.gguf
└── mmproj-model-f16.gguf
```

Na przykład w systemie Linux:

```text
/home/YOUR_USERNAME/models/
├── gemma3_12b/
│   └── google_gemma-3-12b-it-Q4_K_M.gguf
├── llava-v1.6-mistral-7b.Q4_K_M.gguf
└── mmproj-model-f16.gguf
```

Na przykład w systemie Windows:

```text
C:/Users/YOUR_USERNAME/models/
├── gemma3_12b/
│   └── google_gemma-3-12b-it-Q4_K_M.gguf
├── llava-v1.6-mistral-7b.Q4_K_M.gguf
└── mmproj-model-f16.gguf
```

### Wymagania techniczne
W pliku konfiguracyjnym należy ustalić liczbę warstw sieci neuronowej, która zostanie wyładowana na GPU.  
Wartość -1 odpowiada wyładowaniu wszystkich warstw modelu na GPU.  
Im więcej warstw na GPU, tym szybsza inferencja, ale tym więcej potrzeba pamięci karty graficznej.  
Rekomendowana liczba warstw GPU (`n_gpu_layers`) dla wartości VRAM:

| GPU VRAM | Zalecana liczba warstw GPU |
|---|---|
| 3 GB | 5 |
| 4 GB | 8 |
| 6 GB | 15 |
| 8 GB | 25 |
| 12 GB | 32 |
| 16 GB | 35 |
| >=24 GB | -1 |   

Jeśli występuje błąd CUDA memmory, należy zmniejszyć ilość `n_gpu_layers`.

---
## Zastrzeżenie

- Aplikacja jest narzędziem wspomagającym analizę pracy dyplomowej.

- Nie zastępuje ona oceny dokonywanej przez człowieka.

- Wyniki, zwłaszcza ocena merytoryczna, powinny być traktowane jako sugestie i wskazówki.

- Użytkownik jest odpowiedzialny za interpretację i weryfikację wygenerowanych wyników.

- Nie zaleca się korzystania z trybu dokładnego na kartach graficznych innych niż NVIDIA.

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
LaTeX2e/LaTeX3 (pdfLaTeX / XeLaTeX / LuaLaTeX) and runs a battery of automated checks – from line spacing and margins, through grammar and sentence syntax, to bibliography coherence against PN-ISO 690 – returns a PDF with comments and a detailed report file.

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

##### How is the score computed?

The final score is a weighted sum of three components:

$$
\mathrm{Score} = 0.60 \cdot S_{\mathrm{emb}} + 0.20 \cdot S_{\mathrm{pr}} + 0.20 \cdot S_{\mathrm{sota}}
$$

**1. Content–goal coherence ($S_{\mathrm{emb}}$)** — the main component. A summary is generated for each subsection, then the semantic similarity (cosine similarity on embeddings) between the thesis goal $G$ and each subsection summary $T_i$ is computed:

$$
s_i = \cos(\mathrm{emb}(G), \mathrm{emb}(T_i))
$$

Subsections whose similarity does not exceed a threshold $\tau$ are considered weakly related to the goal. If $K$ out of $N$ subsections fall below the threshold:

$$
S_{\mathrm{emb}} = 100 - \frac{K}{N} \cdot 100
$$

The more subsections below the threshold, the lower the score; if all subsections exceed it, $S_{\mathrm{emb}} = 100$.

**2. Direct goal-realisation assessment ($S_{\mathrm{pr}}$)** – the model receives the thesis goal extracted from the beginning of the document and directly judges whether it has been realised across the whole thesis: `100` – goal realised, `50` – partially realised, `0` – not realised.

**3. State-of-the-art review quality ($S_{\mathrm{sota}}$)** – the SOTA section is scored against three rules: it evaluates existing solutions, it identifies a research gap or problem, it provides a synthesis or comparison of methods and approaches. Satisfying at least 2 of the 3 rules gives `100`, exactly 1 rule – `50`, none – `0`.


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

## Installation, setup and usage

### 1. Before running the application

Before starting the analysis, make sure that:

1. The application has been installed or extracted correctly.
2. The `app_config.json` file is present in the correct location.
3. The required local models are available.
4. The PDF file you want to analyze is ready.
5. The correct language of the thesis is selected in the application.

The application should not be run directly from inside a ZIP archive. Extract the package first.

### 2. Configuration file

The application requires a configuration file named:

```text
app_config.json
```

This file is responsible for basic application settings, such as the model directory and hardware mode.

The example files:

```text
cpu_config.json
gpu_config.json
```

are templates only. To use one of them, copy it and rename the copy to:

```text
app_config.json
```

If `app_config.json` is missing or has a different name, the application may not start correctly.

### 3. Model and file locations

The application uses local files stored on the user's computer.

Before running the analysis, make sure that the configuration file points to the correct model directory and that the required model files are available.

### Configuration file location

The configuration file must be placed in the main application directory.

Example:

```text
pdf_diploma_checker/
├── app_config.json
├── cpu_config.json
├── gpu_config.json
├── src/
├── requirements.txt
└── README.md
```

The files:

```text
cpu_config.json
gpu_config.json
```

are only templates. They can be copied and renamed to:

```text
app_config.json
```

### Model directory location

The model directory is defined in `app_config.json` using the field:

```json
"model_dir": "PATH_TO_MODELS_DIR"
```

Example on Windows:

```json
"model_dir": "C:/Users/YOUR_USERNAME/models"
```

Example on Linux:

```json
"model_dir": "/home/YOUR_USERNAME/models"
```

The path should point to the main folder containing all required local model files.

### Required model structure

The model directory should have the following structure:

```text
PATH_TO_MODELS_DIR/
├── gemma3_12b/
│   └── google_gemma-3-12b-it-Q4_K_M.gguf
├── llava-v1.6-mistral-7b.Q4_K_M.gguf
└── mmproj-model-f16.gguf
```

For example, on Linux:

```text
/home/YOUR_USERNAME/models/
├── gemma3_12b/
│   └── google_gemma-3-12b-it-Q4_K_M.gguf
├── llava-v1.6-mistral-7b.Q4_K_M.gguf
└── mmproj-model-f16.gguf
```

For example, on Windows:

```text
C:/Users/YOUR_USERNAME/models/
├── gemma3_12b/
│   └── google_gemma-3-12b-it-Q4_K_M.gguf
├── llava-v1.6-mistral-7b.Q4_K_M.gguf
└── mmproj-model-f16.gguf
```
### Technical requirements

In the configuration file, you need to set the number of neural network layers to be offloaded to the GPU.   
A value of -1 means all of the model's layers are offloaded to the GPU.   
The more layers on the GPU, the faster the inference, but the more GPU memory is required.   
Recommended number of GPU layers (`n_gpu_layers`) per VRAM amount:  
 
| GPU VRAM | Recommended number of GPU layers |
|---|---|
| 3 GB | 5 |
| 4 GB | 8 |
| 6 GB | 15 |
| 8 GB | 25 |
| 12 GB | 32 |
| 16 GB | 35 |
| >= 24 GB | -1 |
 
If a CUDA out-of-memory error occurs, reduce the number of `n_gpu_layers`.

---
## Disclaimer

- The application is a supporting tool for diploma thesis analysis.

- It does not replace human review.

- The results, especially merit assessment, should be treated as suggestions and indicators.

- The user is responsible for interpreting and verifying the generated results.

- Using the detailed mode on non-NVIDIA graphics cards is not recommended.

---
