import json
import os
import datetime

class saving_files:
    def __init__(self, index_path="storage/index.json"):
        self.index_path = index_path
        self.data = self._load_index()

    def _load_index(self):
        #Wczytuje indeks lub tworzy domyślny, jeśli plik jest pusty lub nie istnieje.
        if not os.path.exists(self.index_path) or os.path.getsize(self.index_path) == 0:
            return self._create_initial_index()
        
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            #walidacja
            required_keys = ["prace", "konfiguracje_regul"]
            if not all(key in data for key in required_keys):
                print("Błąd: Niepoprawny format index.json. Przywracanie struktury.")
                return self._create_initial_index()
                
            if "prace" in data:
                data["prace"] = [p for p in data["prace"] if os.path.exists(p['sciezka_lokalna'])]
                
            return data
        except (json.JSONDecodeError, KeyError):
            return self._create_initial_index()
            
        except json.JSONDecodeError:
            print("Ostrzeżenie: Plik index.json jest uszkodzony. Tworzenie nowego.")
            return self._create_initial_index()

    def _create_initial_index(self):
        #Pomocnicza funkcja do tworzenia czystej struktury danych.
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        initial_data = {"prace": [], "konfiguracje_regul": []}
        self._save_to_disk(initial_data)
        return initial_data

    def _save_to_disk(self, data):
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def dodaj_prace(self, nazwa, sciezka, typ):
        if any(p['sciezka_lokalna'] == sciezka for p in self.data["prace"]):
            return
            
        nowy_wpis = {
            "nazwa_pliku": nazwa,
            "sciezka_lokalna": sciezka,
            "typ": typ,
            "data_dodania": datetime.date.today().strftime("%Y-%m-%d")
        }
        self.data["prace"].append(nowy_wpis)
        self._save_to_disk(self.data)
        print(f"Dodano do indeksu: {nazwa}")

    def usun_prace(self, sciezka):
        poczatkowa_ilosc = len(self.data["prace"])
        self.data["prace"] = [p for p in self.data["prace"] if p['sciezka_lokalna'] != sciezka]
        
        if len(self.data["prace"]) < poczatkowa_ilosc:
            self._save_to_disk(self.data)
            print(f"Usunięto plik z indeksu: {sciezka}")

    def zapisz_komentarz(self, sciezka, comment_data):
        for p in self.data["prace"]:
            if p['sciezka_lokalna'] == sciezka:
                if "komentarze" not in p:
                    p["komentarze"] = []
                p["komentarze"].append(comment_data)
                self._save_to_disk(self.data)
                print("Zapisano komentarz do bazy.")
                return

    def pobierz_komentarze(self, sciezka):
        for p in self.data["prace"]:
            if p['sciezka_lokalna'] == sciezka:
                return p.get("komentarze", [])
        return []