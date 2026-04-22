import json
import os
import datetime

class saving_files:
    def __init__(self, index_path=None):
        if index_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.index_path = os.path.join(base_dir, "config", "index.json")
        else:
            self.index_path = index_path
        
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        self.data = self._load_index()

    def _load_index(self):
        if not os.path.exists(self.index_path) or os.path.getsize(self.index_path) == 0:
            return self._create_initial_index()
        
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "prace" not in data:
                data["prace"] = []
            if "konfiguracje_regul" not in data:
                data["konfiguracje_regul"] = []
                
            return data
        except (json.JSONDecodeError, Exception) as e:
            print(f"Błąd odczytu index.json: {e}")
            return self._create_initial_index()

    def _create_initial_index(self):
        initial_data = {"prace": [], "konfiguracje_regul": []}
        self._save_to_disk(initial_data)
        return initial_data

    def _save_to_disk(self, data):
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd zapisu do pliku: {e}")

    def dodaj_prace(self, nazwa, sciezka, typ="PDF"):
        if any(p['sciezka_lokalna'] == sciezka for p in self.data["prace"]):
            return
            
        nowy_wpis = {
            "nazwa_pliku": nazwa,
            "sciezka_lokalna": sciezka,
            "typ": typ,
            "data_dodania": datetime.date.today().strftime("%Y-%m-%d"),
            "komentarze": []
        }
        self.data["prace"].append(nowy_wpis)
        self._save_to_disk(self.data)

    def usun_prace(self, sciezka):
        self.data["prace"] = [p for p in self.data["prace"] if p['sciezka_lokalna'] != sciezka]
        self._save_to_disk(self.data)

    def zapisz_komentarz(self, sciezka, comment_data):
        for p in self.data["prace"]:
            if p['sciezka_lokalna'] == sciezka:
                if "komentarze" not in p:
                    p["komentarze"] = []
                p["komentarze"].append(comment_data)
                self._save_to_disk(self.data)
                return

    def pobierz_komentarze(self, sciezka):
        for p in self.data["prace"]:
            if p['sciezka_lokalna'] == sciezka:
                return p.get("komentarze", [])
        return []