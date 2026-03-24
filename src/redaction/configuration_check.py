'''
Klasa Configuration odpowiedzialna za przechowywanie konfiguracji z wbudowanym 
konstruktorem parsującym dane z pliku json oraz walidującym.
Klasa ConfigValidationError to niestandardowy wyjątek do obsługi błędów walidacji konfiguracji.
Klasa Validator do sprawdzania błędów pdf'a na podstawie konfiguracji
 '''

from bare_struct import DocumentData
import json
import logging # proponuje omówić wspólne mechanizmy logów do błędów i debugowania ~Bartek 24.03
from dataclasses import dataclass
from typing import List

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

@dataclass     
class Issue:
    category: str
    description: str
    page: int
    xy: tuple

class Validator:
    def __init__(self, config: Configuration):
        self.config = config
        self.issues = [] # lista błędów

    def validate_pdf(self, doc_data: DocumentData) -> List[str]:
        pass

    def check_page_count(self, doc_data: DocumentData) -> bool:
        page_count = doc_data.get_page_count()
        if page_count < self.config.min_stron:
            self.issues.append(Issue(
                category="Strony",
                description=f"Dokument ma {page_count} stron, mniej niż minimalna liczba {self.config.min_stron}",
                page=0,
                xy=(0, 0)
            ))
            return False
        elif page_count > self.config.max_stron:
            self.issues.append(Issue(
                category="Strony",
                description=f"Dokument ma {page_count} stron, więcej niż maksymalna liczba {self.config.max_stron}",
                page=0,
                xy=(0, 0)
            ))
            return False
        else:
            logging.info(f"Redaction: liczba stron {page_count} jest w dozwolonym zakresie")
            return True
    
    def check_font_size(self, doc_data: DocumentData) -> bool:
        most_used_font_size = max(doc_data.get_font_size_usage(), key=doc_data.get_font_size_usage().get, default=None)
        if most_used_font_size is None:
            logging.warning("Redaction: nie można określić rozmiaru czcionki")
            return True
        elif most_used_font_size != self.config.font_size:
            self.issues.append(Issue(
                category="Czcionka",
                description=f"Rozmiar czcionki: {most_used_font_size}, oczekiwany: {self.config.font_size}",
                page=0,
                xy=(0, 0)
            ))
            return False
        else:
            logging.info(f"Redaction: rozmiar czcionki {most_used_font_size} jest zgodny z wymaganiami")
            return True

	def check_justification(self, doc_data: DocumentData) -> bool:
        expected_justified = self.config.justowanie
        issues_found = False

        for page in doc_data.pages:
            for block in page.text_blocks:
                lines = block.lines
            
                if len(lines) <= 1:
                    continue
            
                for i in range(len(lines) - 1):
                    line = lines[i]

                    if not line.spans:
                        continue

                    is_justified = (
                        line.alignement == "justified" 
                    )

                    if expected_justified and not is_justified:
                        self.issues.append(Issue(
                            category="Justowanie",
                            description=f"Brak justowania w akapicie (linia {i+1})",
                            page=page.number,
                            xy=line.bbox[:2]
                        ))
                        issues_found = True

                    elif not expected_justified and is_justified:
                        self.issues.append(Issue(
                            category="Justowanie",
                            description=f"Tekst jest wyjustowany, a nie powinien (linia {i+1})",
                            page=page.number,
                            xy=line.bbox[:2]
                        ))
                        issues_found = True

        if not issues_found:
            logging.info("Redaction: justowanie zgodne z wymaganiami")

        return not issues_found

	    
