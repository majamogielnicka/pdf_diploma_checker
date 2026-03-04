# MILESTONES:

Metryka zgodna z założeniami projektowymi, mierzona na datasecie 10 przykładowych prac (z wyjątkiem Milestone 1, gdzie część metryk mierzona jest na podstawie danych testowych (mock data)). 

## Milestone 1: 25.03.2026
- Wydobywanie bloków tekstu do ustalonego formatu – w tym wydobywanie współrzędnych X,Y, wielkości i typu czcionki, detekcja marginesów i justowania, weryfikacja interlinii, zliczanie całkowitej liczby stron dokumentu oraz klasyfikacja bloków tekstu (np. nagłówek, stopka) z pliku PDF, analiza zgodności pracy z przyjmowanym plikiem JSON. \
Kryterium skuteczności: F1 ≥ 0,90; precyzja ≥ 0,85
- Weryfikacja interpunkcji, sprawdzanie podwójnych spacji, myślników oraz spójności zapisu symboli dziesiętnych. \
Kryterium skuteczności: F1 ≥ 0,85; czułość ≥ 0,80
- Lokalne modele językowe są skonfigurowane. Modele poprawnie ekstraktują cel pracy oraz wykrywają fragmenty odnoszące się do SOTA na podstawie charakterystycznych fraz.\
Kryterium skuteczności: Ssota ≥ 33%
- Działający system antyplagiatowy, czyli otwieranie wyników zaznaczonego fragmentu (do określonej liczby znaków) w wyszukiwarce. 

## Milestone 2: 22.04.2026
Inicjowanie działania poszczególnych modułów przez skrypt główny. 
- Wykrywanie błędów typograficznych (sierotki, wdowy, bękarty, korytarze) \
Kryterium skuteczności: F1 ≥ 0,85; czułość ≥ 0,80 
- Analiza składni zdań w formie procentowej liczby wystąpienia odpowiednich struktur zdań, weryfikacja definicji skrótów przy pierwszym użyciu oraz weryfikacja poprawności ortograficznej. \
Kryterium skuteczności: dla języka F1 ≥ 0,85; precyzja ≥ 0,80; Maksymalnie jeden fałszywy błąd na stronę tekstu
- Wprowadzenie metryki oceny merytoryki. Ocena obecności i jakość przeglądu stanu wiedzy (SOTA) \
Kryterium skuteczności: Sgoal ≥ 60%
- Parsowanie struktury JSON i nakładanie adnotacji na dokument wynikowy PDF. 

## Milestone 3: 20.05.2026
Integracja modułów w aplikacji desktopowej
- Wczytywanie danych wejściowych, analiza oraz generowanie PDF wyjściowego z naniesionymi komentarzami.
Obsługa trybów szybkiego i dokładnego. \
Kryterium skuteczności: czas wykonywania trybu szybkiego niewiększy niż 5 minut; szacowany czas wykonywania trybu pełnego dla pracy 40 - 60 stron niewiększy niż 40 min. \
- Weryfikacja dostosowania się do normy bibliograficznej (PN-ISO 690:2012) oraz wykrywanie braku spójności odnośników do literatury wewnątrz tekstu. \
Kryterium skuteczności: F1 ≥ 0,90; precyzja ≥ 0,85;
- Generowanie podsumownaia bibliografii oraz weryfikacja obecności słowa "Źródło:" przy rysunkach, które nie są wykresami. \
- Wykrycie obrazów w grafice rastrowej. Weryfikacja poprawności odnoszenia się przez autora do wykresów. Detekcja niespójności czcionek na różnych wykresach. \
Kryterium skuteczności: F1 ≥ 0,80; precyzja ≥ 0,75;
- Kryterium skuteczności: Sgoal ≥ 70%

## Deadline: 3.06.2026
Wdrożenie obsługi błędów napotkanych podczas testowania aplikacji.
Czas realizacji analizy w trybie szybkim nie przekracza 5 minut.
Szacowany czas realizacji analizy w trybie pełnym nie przekracza 40 minut.
