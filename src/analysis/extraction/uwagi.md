commit 09.03 Bartek
nie miałem żadnych problemów z polskimi znakami przy ekstrakcji. inspirowałem się funkcją Dodo, ale ogólna koncepcja się kompletnie zmieniła. Przeczytajcie kod i dodajcie swoje uwagi.
aha i dodałem brancha na ktorym jest ten commit, proponuje na każde pomniejsze zadanie tworzyć oddzielnego brancha, zeby wygodniej sie pisalo razem. Wszyscy muszą wiedzieć jak się używa branchy, żeby nic się nie popsuło.
pozdrawiam.

commit 23.03 Bartek
sprzątam bałagan: 
-usuwam basic_pdf_extractor.py, ostatni commit tam (oprócz Maji) jest sprzed 2 tygodni, zakładam, że nikt na nim nie pracuje,
-przeniosłem całą główną strukturę do bare_struct.py, funkcje do niej zostają w extraction_json.py,
-opisałem mniej więcej wszystkie pliki,
-z prawie każdego pliku usunąłem wszystko co było poza funkcjami i strukturami, przykład użycia można zobaczyć w example_usage.py, wszystkie inne pliki traktujmy jako biblioteki (do importowania a nie odpalania),
-nie wiem co zrobić z extraction_txt