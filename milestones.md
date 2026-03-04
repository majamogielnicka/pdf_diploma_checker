# MILESTONES:

Metryka zgodna z założeniami projektowymi, mierzona na datasecie 10 przykładowych prac (z wyjątkiem Milestone 1, gdzie część metryk mierzona jest na podstawie danych testowych (mock data)). 

## Milestone 1: 25.03.2026
- Wydobywanie bloków tekstu do ustalonego formatu – w tym wydobywanie współrzędnych X,Y, wielkości i typu czcionki, detekcja marginesów i justowania, weryfikacja interlinii, zliczanie całkowitej liczby stron dokumentu oraz klasyfikacja bloków tekstu (np. nagłówek, stopka) z pliku PDF, analiza zgodności pracy z przyjmowanym plikiem JSON. \
Kryterium skuteczności: F1 ≥ 0,90; precyzja ≥ 0,85
- Weryfikacja interpunkcji, sprawdzanie podwójnych spacji, myślników oraz spójności zapisu symboli dziesiętnych. \
Kryterium skuteczności: F1 ≥ 0,85; czułość ≥ 0,80
- Lokalne modele językowe są skonfigurowane. Modele poprawnie ekstraktują cel pracy oraz wykrywają fragmenty odnoszące się do SOTA na podstawie charakterystycznych fraz.\
Kryterium skuteczności: Sgoal ≥ 20%
- Działający system antyplagiatowy, czyli otwieranie wyników zaznaczonego fragmentu w wyszukiwarce. \

## Milestone 2: 22.04.2026
Inicjowanie działania poszczególnych modułów przez skrypt główny. 
- Wykrywanie błędów typograficznych (sierotki, wdowy, bękarty, korytarze) \
Kryterium skuteczności: F1 ≥ 0,85; czułość ≥ 0,80 
- Analiza składni zdania w formie procentowej liczby wystąpienia odpowiednich struktur zdań, weryfikacja definicji skrótów przy pierwszym użyciu oraz weryfikacja poprawności ortograficznej. \
Kryterium skuteczności: dla języka F1 ≥ 0,85; precyzja ≥ 0,80; Maksymalnie jeden fałszywy błąd na stronę tekstu
- Wprowadzenie metryki oceny merytoryki. Ocena obecności i jakość przeglądu stanu wiedzy (SOTA) \
Kryterium skuteczności: Sgoal ≥ 50%
- Parsowanie struktury JSON i nakładanie adnotacji na dokument wynikowy PDF. \

## Milestone 3: 20.05.2026
Integracja modułów w aplikacji desktopowej
- Wczytywanie danych wejściowych, analiza oraz generowanie raportu końcowego.
Obsługa trybów szybkiego i dokładnego. \
Kryterium skuteczności: czas wykonywania trybu szybkiego mniejszy niż 5 minut; czas wykonywania trybu dokładnego dla pracy 40 - 60 stron w zakresie 15 do 40 min dla CPU oraz 8 do 20 min dla GPU 8GB VRAM 
- Weryfikacja normy bibliograficznej (PN-ISO 690:2012) oraz ocena spójności odnośników wewnątrz tekstu. \
Kryterium skuteczności: F1 ≥ 0,90; precyzja ≥ 0,85 dla werufikacji normy biograficznej i F1 ≥ 0,80; precyzja ≥ 0,85 dla spójności odnośników wewnątrz tekstu
- Generowanie statystyk bibliografii oraz kontrola praw autorskich (weryfikacja obecności słowa "Źródło:" przy obiektach graficznych). \
- Generowanie błędów oraz niespójności dotyczących wykresów oraz obrazów. \
Kryterium skuteczności: Sgoal ≥ 70%

## Deadline: 3.06.2026
Wdrożenie obsługi błędów napotkanych podczas testowania aplikacji.
Czas realizacji analizy w trybie szybkim nie przekracza 5 minut.
