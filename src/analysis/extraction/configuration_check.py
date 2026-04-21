'''
Klasa Configuration odpowiedzialna za przechowywanie konfiguracji z wbudowanym 
konstruktorem parsującym dane z pliku json oraz walidującym.
Klasa ConfigValidationError to niestandardowy wyjątek do obsługi błędów walidacji konfiguracji.
Klasa Validator do sprawdzania błędów pdf'a na podstawie konfiguracji
 '''

from src.analysis.extraction.bare_struct import DocumentData
import json
import logging # proponuje omówić wspólne mechanizmy logów do błędów i debugowania ~Bartek 24.03
from dataclasses import dataclass
from typing import List

class ConfigValidationError(Exception):
    #TODO jak mówię o systemie błędów to mam na myśli (błędy opisane zrozumiale dla nas)
    pass



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
        self.issues.clear() # czyścimy poprzednie błędy

        self.check_interline_spacing(doc_data)
        self.check_page_count(doc_data)
        self.check_font_size(doc_data)
        self.check_margins(doc_data)
        self.check_orientation(doc_data)
        self.check_fonts(doc_data)
        self.check_justification(doc_data)
        self.check_format(doc_data)

        return [f"{issue.category}: {issue.description} (strona {issue.page})" for issue in self.issues]

    def check_interline_spacing(self, doc_data: DocumentData) -> bool:
        line_spacing = doc_data.get_dominant_line_spacing()
        if line_spacing is None:
            logging.warning("Redaction: nie można określić interlinii")
            return True
        elif abs(line_spacing - self.config.interlinia) > 0.1: # dopuszczalna różnica 0.1
            self.issues.append(Issue(
                category="Interlinia",
                description=f"Interlinia: {line_spacing}, oczekiwana: {self.config.interlinia}",
                page=0,
                xy=(0, 0)
            ))
            return False
        else:
            logging.info(f"Redaction: interlinia {line_spacing} jest zgodna z wymaganiami")
            return True
        
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
        elif abs(most_used_font_size - self.config.font_size) > 0.1: # dopuszczalna różnica 0.1
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

    def check_margins(self, doc_data: DocumentData) -> bool:
        margins = doc_data.get_margins()
        if not margins:
            logging.warning("Redaction: nie można określić marginesów")
            return True
        if self.config.margin_type == "lustrzany":
            if len(margins) < 2:
                logging.warning("Redaction: zbyt mało stron do oceny marginesów lustrzanych")
                return True
            
            for page_num, margin in margins.items():
                if page_num % 2 == 1: # strona nieparzysta
                    if margin.get("left", 0) <= margin.get("right", 0):
                        self.issues.append(Issue(
                            category="Marginesy",
                            description=f"Strona {page_num}: oczekiwany większy margines po lewej stronie: left={margin.get('left', 0)}, right={margin.get('right', 0)}",
                            page=page_num,
                            xy=(0, 0)
                        ))
                        return False
                else: # strona parzysta
                    if margin.get("right", 0) <= margin.get("left", 0):
                        self.issues.append(Issue(
                            category="Marginesy",
                            description=f"Strona {page_num}: oczekiwany większy margines po prawej stronie: left={margin.get('left', 0)}, right={margin.get('right', 0)}",
                            page=page_num,
                            xy=(0, 0)
                        ))
                        return False
                    margins[page_num]["left"], margins[page_num]["right"] = margins[page_num]["right"], margins[page_num]["left"]
            
            org_margin = margins[1]
            for page_num, margin in margins.items():
                if margin != org_margin:
                    self.issues.append(Issue(
                        category="Marginesy",
                        description=f"Strona {page_num}: marginesy różnią się od innych stron: {margin} vs {org_margin}",
                        page=page_num,
                        xy=(0, 0)
                    ))
                    return False
            logging.info("Redaction: marginesy lustrzane są zgodne na wszystkich stronach")
            return True

    def check_format(self, doc_data: DocumentData) -> bool:
        tolerance = 10

        formats = {
            "A5": (420, 595),
            "A4": (595, 842),
            "A3": (842, 1191)
        }

        if self.config.format not in formats:
            logging.warning("Redaction: nieznany format strony w konfiguracji")
            return False
        exp_w,exp_h = formats[self.config.format]
        for page_num, (width,height) in doc_data.get_page_dimensions().items():
            if not ((abs(width - exp_w)<=tolerance and abs(height-exp_h)<=tolerance) or (abs(width-exp_h)<=tolerance and abs(height-exp_w)<=tolerance)):
                self.issues.append(Issue(
                    category="Format",
                    description = f"Strona {page_num}: oczekiwany format {self.config.format}, wymiary strony: {width} x {height}",
                    page = page_num,
                    xy = (0, 0)
                ))
                return False
        logging.info("Redaction:format stron jest zgodny z wymaganiami")
        return True
    
    def check_orientation(self, doc_data: DocumentData) -> bool:
        doc_data.get_page_dimensions()
        for page_num, (width, height) in doc_data.get_page_dimensions().items():
            if self.config.orientation == "pionowa" and width > height:
                self.issues.append(Issue(
                    category="Orientacja",
                    description=f"Strona {page_num}: oczekiwana orientacja pionowa, wymiary strony: {width}x{height}",
                    page=page_num,
                    xy=(0, 0)
                ))
                return False
            elif self.config.orientation == "pozioma" and height > width:
                self.issues.append(Issue(
                    category="Orientacja",
                    description=f"Strona {page_num}: oczekiwana orientacja pozioma, wymiary strony: {width}x{height}",
                    page=page_num,
                    xy=(0, 0)
                ))
                return False
        logging.info("Redaction: orientacja stron jest zgodna z wymaganiami")
        return True

    def check_fonts(self, doc_data: DocumentData) -> bool:
        font_usage = doc_data.get_font_usage()
        if not font_usage:
            logging.warning("Redaction: nie można określić używanych czcionek")
            return True
        for font in font_usage.keys():
            if font not in self.config.font_list:
                self.issues.append(Issue(
                    category="Czcionka",
                    description=f"Używana czcionka '{font}' nie jest dozwolona",
                    page=0,
                    xy=(0, 0)
                ))
                return False
        logging.info("Redaction: wszystkie używane czcionki są dozwolone")
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

	    
