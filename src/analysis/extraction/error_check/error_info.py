'''Konwersja outputu converter_linguistics na output błędów'''

import json
from typing import List, Dict, Any

class ErrorChecker:
    def __init__(self):
        self.errors = []
        self.error_counter = 1

    # Generowanie unikalnych ID
    def _generate_id(self) -> str:
        err_id = f"ERR_{self.error_counter:03d}"
        self.error_counter += 1
        return err_id

    # Główna metoda sprawdzająca, czy w danym bloku (TODO: linijce może też) jest flaga z błędem
    def check_document(self, document) -> List[Dict[str, Any]]:
        """
        Główna metoda sprawdzająca. Przelatuje przez zmapowany dokument
        i weryfikuje różne flagi błędów na blokach.
        """
        for block in document.logical_blocks:
            
            # Sprawdzanie tylko dla paragrafów
            if getattr(block, "type", "") == "paragraph":
                
                # Flaga: wdowy
                widow_which =  getattr(block, "is_widow", 0)
                if widow_which > 0:    
                    self._handle_widow(block, widow_which)
                
                # Flaga: sieroty...


        return self.errors

    # Formatowanie komentarza dla wdów
    def _handle_widow(self, block, widow_which):
        if not block.words:
            return

        widow_words = block.words[-widow_which:]
        last_word = widow_words[0]
        found_text = " ".join([w.text for w in widow_words])
        
        error_entry = {
            "id": self._generate_id(),
            "modul": "REDAKCJA",
            "kategoria": "typografia",  #
            "strona": last_word.page_number,
            "wspolrzedne": {
                "x": round(last_word.bbox[0], 2), 
                "y": round(last_word.bbox[1], 2)  
            },
            "znaleziony_tekst": found_text,
            "sugestia": "",
            "komentarz": "Wykryto wdowę"
        }
        self.errors.append(error_entry)

    def save_to_json(self, file_path: str):
        output_data = {
            "wykryte_bledy": self.errors
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)