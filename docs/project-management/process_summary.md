# Podsumowanie procesu pracy

## Cel projektu
Stworzenie systemu oceniającego prace dyplomowe, który na wejście przyjmuje plik konfiguracyjny z wymaganiami wraz z pracą dyplomową, zwraca plik pdf z komentarzami wskazującymi błędy różnych kategorii, wyświetla ocenę merytoryczną oraz dodatkowe informacje w panelu użytkownika.


## Co udało się zrealizować
- Zdecydowaną większość założeń z pliku Pełne_założenia.md
- Opracowano założenia projektu
- Opracowano wzór na ocenę merytoryczną 
- Wykorzystano różne technologie w projekcie (lokalne LLM-y, słowniki pythonowe)
- Przygotowano plik README.md oraz foldery `src`, `docs`, `images`.
- Przygotowano pliki wykonywalne dla Linuxa oraz Windowsa.

## Co sprawiło problemy
- Opracowanie oceny merytorycznej bez odpowiedniego sprzętu było uciążliwe

## Czego nie udało się zrobić
- Wykrywanie błędu typograficznego - korytarze
- Brak wykrywania podmiotu w zdaniu, jeśli jest to dopełniacz liczby mnogiej (wynika z wyboru słownika).

## Wnioski
Podczas pracy okazało się, że ważne jest utrzymywanie czytelnej struktury projektu, zapisywanie zależności w `requirements.txt` oraz regularne aktualizowanie dokumentacji. W przyszłości warto wcześniej zaplanować strukturę katalogów i sposób testowania aplikacji.
Przy rozdzielaniu zadań między osobami kontrybuującymi, warto rozważać możliwości sprzętowe członków projektu. 


## Możliwe usprawnienia
- Lepsze dostosowanie systemu do innych uczelni (osobne modele embeddingowe dla różnych tematyk prac).
- Rozbudowanie dokumentacji instalacji.
- Dokładniejsza obsługa sprawdzania biboliografii.
- Panel użytkownika po angielsku.