# ZAŁOŻENIA PROJEKTOWE

## 1. Cel projektu

Celem projektu jest opracowanie systemu do automatycznej analizy pracy dyplomowej w formacie PDF wygenerowanej z:
- MS Word Online / Office 365
- MS Word 2019 lub nowszy
- LaTeX (różne kompilatory, np. pdfLaTeX/XeLaTeX/LuaLaTeX)

System ma wykrywać błędy w pracy oraz generować plik PDF z komentarzami wskazującymi znalezione problemy.

## 2. Forma działania systemu

System będzie działał jako lokalna aplikacja desktopowa (GUI) uruchamiana na komputerze użytkownika w środowisku Windows/Linux.

## 3. Zakres funkcjonalny systemu

### 3.1. Wejście / wyjście

**Wejście:**
- 1 plik PDF pracy dyplomowej
- plik konfiguracyjny reguł (YAML)
- język (PL/EN)

**Wyjście:**
- PDF z naniesionymi komentarzami

### 3.2. Analiza językowa (PL/EN)

System sprawdza:
- gramatykę, ortografię, interpunkcję
- strukturę zdań (obecność podmiotu i orzeczenia)
- stronę zdań (identyfikacja strony biernej)

**Kryteria mierzalne:**
- Obsługa języków: PL i EN
- Skuteczność wykrywania błędów językowych: 85% - 90%

### 3.3. Analiza redakcyjna podstawowa (zgodność z wytycznymi PG) — skuteczność 90%

System sprawdza:
- liczbę stron tekstu:
  - inż.: 40–50
  - mgr: 60–80
- format i układ dokumentu:
  - format A4
  - orientacja pionowa
  - podstawowa czcionka
  - wielkość czcionki podstawowej: 10 pt
  - interlinia: 1.5
  - tekst wyjustowany
  - marginesy lustrzane
  - numeracja stron ciągła, w stopce, bez numeru na stronie tytułowej
  - brak pustych stron
- elementy redakcyjne:
  - podpis tabeli nad tabelą
  - podpis rysunku pod rysunkiem
  - przywołanie wszystkich tabel/rysunków/cytowań w tekście
  - definicja terminu/skrótu przy pierwszym użyciu
  - bibliografia zgodna z PN-ISO 690:2012 (zakres reguł konfigurowalny)

### 3.4. Analiza redakcyjna rozszerzona — skuteczność 85%

System sprawdza:
- szewce, bękarty, sierotki, wdowy, korytarze (w zakresie możliwym na podstawie layoutu PDF)
- symbole dziesiętne (spójność zapisu)
- spójność odnośników do rysunków/tabel
- rozpoczynanie rozdziałów od nowej strony
- podwójne spacje
- łączniki i myślniki
- cudzysłowy
- przecinki i kropki w listach
- cytaty
- inne błędy edycyjne zdefiniowane w pliku reguł

### 3.5. Analiza wizualna — skuteczność 75%

System analizuje:
- jakość grafik (w tym odróżnienie grafiki rastrowej/wektorowej)
- czy wykresy mają podpisane osie i jednostki
- spójny rozmiar czcionki na wykresach
- podstawową kontrolę praw autorskich (np. brak podpisów/źródeł przy rysunkach)

### 3.6. Analiza merytoryczna (LLM lokalny) — skuteczność 75%

System (lokalny model LLM) sprawdza, czy praca zawiera:
- aspekt teoretyczny
- SOTA / przegląd stanu wiedzy
- metodologię
- opis opracowanej koncepcji
- jednoznacznie wpisany cel pracy
- potwierdzenie realizacji celu

### 3.7. Analiza bibliografii — skuteczność 80%

System wykonuje:
- analizę spójności zapisu (sortowanie, spójna forma imion oraz nazwisk)
- generowanie podsumowania bibliografii

### 3.8. Plagiat (fragmentowy) — skuteczność 80%

System sprawdza, czy wskazane fragmenty lub losowo wybrane zdania:
- występują w źródłach internetowych (wyszukiwarka)
- są potencjalnie skopiowane

Analiza tylko fragmentów:
- wskazanych przez użytkownika lub
- max. N losowych zdań (np. N=10) na jedno uruchomienie

Raport zawiera:
- zdanie/frazę
- znalezione źródło

## 4. Wymaganie dotyczące adnotacji PDF (wyjście)

Każdy wykryty problem musi zostać zapisany jako komentarz/adnotacja zawierająca:
- kategorię błędu (językowy, redakcyjny, wizualny, merytoryczny, bibliografia, plagiat)
