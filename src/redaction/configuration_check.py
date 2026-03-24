'''
Jest to zbiór funkcji sprawdzających poprawność PDF'a z plikiem konfiguracyjnym.
Z założenia będą one używać wielu metod z naszych struktur, które, jak zakładam,
będą powstawały w trakcie pisania i udoskonalania tych właśnie funkcji.
Oczywiście oprócz tego znajduje się tutaj cały parser pliku konfiguracyjnego.
 '''

from bare_struct import *
import json
import logging # proponuje omówić wspólne mechanizmy logów do błędów i debugowania ~Bartek 24.03

class ConfigValidationError(Exception):
    #TODO jak mówię o systemie błędów to mam na myśli (błędy opisane zrozumiale dla nas)
    pass

@dataclass
class Configuration:
    interlinia: float
    min_stron: int
    max_stron: int
    font_size: int
    margin_type: str
    format: str
    orientation: str
    justowanie: bool
    font_list: List[str]

    def __init__(self, config_path: str):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._validateAndAssign(data)
            
            logging.info(f"Konfiguracja załadowana pomyślnie z {config_path}")
            
        except FileNotFoundError:
            raise FileNotFoundError(f"nie znaleziono konfiguracji {config_path}")
        except json.JSONDecodeError:
            raise ConfigValidationError(f"nieporpawny format jsona {config_path}")
    
    def _validateAndAssign(self, data: dict):
        try:
            self.interlinia = float(data["interlinia"])
            self.min_stron = int(data["minimalna_liczba_stron"])
            self.max_stron = int(data["maksymalna_liczba_stron"])
            self.font_size = int(data["rozmiar_czcionki"])
            
            if self.min_stron > self.max_stron:
                raise ConfigValidationError("min_stron > max_stron, błąd konfiguracji")

            if data["margines"].lower() not in ["lustrzany", "standardowy"]:
                raise ConfigValidationError("błędny margines, oczekiwano 'lustrzany' lub 'standardowy'")
            self.margin_type = data["margines"]

            self.format = data["format"]

            if data["orientacja"].lower() not in ["pionowa", "pozioma"]:
                raise ConfigValidationError("błędna orientacja, oczekiwano 'pionowa' lub 'pozioma'")
            self.orientation = data["orientacja"]

            if data["justowanie"].lower() not in ["tak", "nie"]:
                raise ConfigValidationError("błędne justowanie, oczekiwano 'tak' lub 'nie'")
            self.justowanie = data["justowanie"].lower() == "tak"

            czcionki_dict = data.get("czcionka", {})
            self.font_list = list(czcionki_dict.values())
            
            if not self.font_list:
                logging.warning("brak dozwolonych czcionek w konfiguracji")

        except KeyError as e:
            raise ConfigValidationError(f"brakujący klucz w konfiguracji: {e}")
        except ValueError as e:
            raise ConfigValidationError(f"niepoprawny typ danych w konfiguracji: {e}")