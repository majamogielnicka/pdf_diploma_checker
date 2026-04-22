'''
Znajduje się tu główna klasa RedactionValidator, która zajmuje się
...walidowaniem...
pdf'a pod względem błędów z redakcji i "zaawansowanej" redakcji.

'''

from src.analysis.extraction.bare_struct import DocumentData
from src.analysis.extraction.schema import FinalDocument
from src.common.errors.error_struct import Error, FileError, Module
from dataclasses import dataclass
from typing import List
import json
import logging

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
            raise FileError(f"nieporpawny format jsona {config_path}")
    
    def _validateAndAssign(self, data: dict):
        try:
            self.interlinia = float(data["interlinia"])
            self.min_stron = int(data["minimalna_liczba_stron"])
            self.max_stron = int(data["maksymalna_liczba_stron"])
            self.font_size = int(data["rozmiar_czcionki"])
            
            if self.min_stron > self.max_stron:
                raise FileError("min_stron > max_stron, błąd konfiguracji")

            if data["margines"].lower() not in ["lustrzany", "standardowy"]:
                raise FileError("błędny margines, oczekiwano 'lustrzany' lub 'standardowy'")
            self.margin_type = data["margines"]


            if data["format"].lower() not in ["a3", "a4", "a5"]:
                raise FileError("błędny format strony, oczekiwano 'a3', 'a4' lub 'a5'")
            self.format = data["format"]

            if data["orientacja"].lower() not in ["pionowa", "pozioma"]:
                raise FileError("błędna orientacja, oczekiwano 'pionowa' lub 'pozioma'")
            self.orientation = data["orientacja"]

            if data["justowanie"].lower() not in ["tak", "nie"]:
                raise FileError("błędne justowanie, oczekiwano 'tak' lub 'nie'")
            self.justowanie = data["justowanie"].lower() == "tak"

            czcionki_dict = data.get("czcionka", {})
            self.font_list = list(czcionki_dict.values())
            
            if not self.font_list:
                logging.warning("brak dozwolonych czcionek w konfiguracji")

        except KeyError as e:
            raise FileError(f"brakujący klucz w konfiguracji: {e}")
        except ValueError as e:
            raise FileError(f"niepoprawny typ danych w konfiguracji: {e}")

class RedactionValidator:
    def __init__(self, document_data: DocumentData, document_data_linguistics: FinalDocument, config_path: str = None):
        self.document_data = document_data
        self.document_data_linguistics = document_data_linguistics
        if config_path is not None:
            self.config = Configuration(config_path)
        else:
            self.config = None

        self.module = Module.REDACTION
        self.id_counter = 0
        self.errors = []

    def _get_next_id(self):
        id = f"ERR_RED_{self.id_counter}"
        self.id_counter += 1
        return id

    def validate(self, config_ckeck: bool = True, basic_redaction_check: bool = True, advanced_redaction_check: bool = True):
        self.errors.clear() #metody indywidualnie wrzucaja errory na stos
        self.id_counter = 0
        #--------------------config check
        if self.config is not None and config_ckeck:
            self.check_interline_spacing(self.document_data)
            self.check_page_count(self.document_data)
            self.check_font_size(self.document_data)
            self.check_margins(self.document_data)
            self.check_orientation(self.document_data)
            self.check_fonts(self.document_data)
            self.check_justification(self.document_data)
            self.check_format(self.document_data)

        #--------------------basic redaction check
        if basic_redaction_check:
            self.check_blank_page()

        #--------------------advanced redaction check
        if advanced_redaction_check:
            self.check_orphans()
            self.check_widows()
            self.check_bekarts()
            self.check_szewce()
            self.check_korytarze()

        '''
        if not is_toc:
            error = Error(
                id = self._get_next_id(),
                module=self.module,
                category = "TOC_lack",
                page_nr = 1,
                bounding_box = (self.document_data.pages[0].width - 60, 10, self.document_data.pages[0].width - 10, 60), 
                text = None,
                comments = f"Wykryto brak spisu treści."
            )
            errors.append(error)
        else:
            for entry in wrong_toc_entries:
                error = Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "TOC_mismatch",
                    page_nr = entry.page,
                    bounding_box = entry.bbox,
                    text = entry.title,
                    comments = f"Rozdział/Podrozdział '{entry.title}' nie znajduje się na wskazanej stronie (strona {entry.page})."
                )
                errors.append(error) 

        page_1_footer_bbox, lack_of_footers = self.check_footers()
        if page_1_footer_bbox:
            error = Error(
                id = self._get_next_id(),
                module = self.module,
                category = "Footer_on_1st_page",
                page_nr = 1,
                bounding_box = page_1_footer_bbox, 
                text = "1",
                comments = "Wykryto numerację na pierwszej stronie, która nie powinna się tam znaleźć."
            )
            errors.append(error) 

        for number in lack_of_footers:
            error = Error(
                id = self._get_next_id(),
                module = self.module,
                category = "No_footer",
                page_nr = number,
                bounding_box = (self.document_data.pages[number - 1].width/2 - 20, 
                                self.document_data.pages[number - 1].height - 40, 
                                self.document_data.pages[number - 1].width/2 + 20, 
                                self.document_data.pages[number - 1].height - 10),
                text = None,
                comments = f"Wykryto brak numeracji lub niepoprawną numerację na stronie {number}"
            )
            errors.append(error)




        converter_errors = self.check_from_converter()
        errors.extend(converter_errors)
        '''
        return self.errors
    
    def last_errors_to_json(self):
        return json.dumps([error.__dict__ for error in self.errors], ensure_ascii=False, indent=4)
    
    def last_errors_to_file(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.last_errors_to_json())

    def check_orphans(self):
        '''Zwraca listę sierot (spans)'''
        orphans = []
        for page in self.document_data.pages:
            for block in page.text_blocks:
                for line in block.lines:
                    if line.spans is None or len(line.spans) == 0:
                        continue
                    last_span = None
                    for span in line.spans[::-1]:
                        if span.text.strip() == "":
                            continue
                        last_span = span
                        break
                    if last_span is None:
                        continue
                    if len(last_span.text) == 1:
                        if last_span.text < 'a' or last_span.text > 'z':
                            continue

                        if last_span.size < self.document_data.get_most_common_font_size() * 0.8:
                            continue
                        orphans.append(last_span)
                        self.errors.append(Error(
                            id = self._get_next_id(),
                            module = self.module,
                            category = "orphan_span",
                            page_nr = page.number,
                            bounding_box = last_span.bbox,
                            text = last_span.text,
                            comments = "Wykryto sierotę - pojedynczy znak na końcu linii, który może zostać oderwany od reszty tekstu podczas redakcji."
                        ))
        return orphans
    
    def check_korytarze(self):
        korytarze = []
        for page in self.document_data.pages:
            if page < 3:
                continue
            for block in page.text_blocks:
                if block.lines is None or len(block.lines) <= 1:
                    continue
                
                paths_to_check = []
                first_line = block.lines[0]
            
                if first_line.spans and len(first_line.spans) >= 2:
                    for i in range(len(first_line.spans) - 1):
                        span = first_line.spans[i]
                        next_span = first_line.spans[i + 1]
                        paths_to_check.append((span.bbox[2], next_span.bbox[0]))
                
                for line in block.lines[1:]:
                    if not line.spans:
                        continue
                        
                    for span in line.spans:
                        for (x1, x2) in paths_to_check:
                            if (span.bbox[0] > x1 and span.bbox[0] < x2) or (span.bbox[2] > x1 and span.bbox[2] < x2):
                                korytarze.append(span)
                                self.errors.append(Error(
                                    id = self._get_next_id(),
                                    module = self.module,
                                    category = "korytarz",
                                    page_nr = page.number,
                                    bounding_box = (x1, span.bbox[1] - 15, x2, span.bbox[3]),
                                    text = None,
                                    comments = "Wykryto korytarz (nakładające się przerwy między wyrazami w sąsiednich liniach)."
                                ))
                    
                    paths_to_check = []
                    if len(line.spans) >= 2:
                        for i in range(len(line.spans) - 1):
                            s = line.spans[i]
                            ns = line.spans[i + 1]
                            paths_to_check.append((s.bbox[2], ns.bbox[0]))
                            
        return korytarze

    def check_blank_page(self):
        blank_pages = []
        for page in self.document_data.pages:
            if page.is_blank == True:
                blank_pages.append(page)
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "blank_page",
                    page_nr = page.number,
                    bounding_box = (0,0,0,0),
                    text = "",
                    comments = "Pusta strona"
                ))

        return blank_pages
    
    # Funkcja sprawdzająca błędy zapisane jako flagi przez converter_linguistics
    def check_from_converter(self):
        converter_errors = []
        for block in self.document_data_linguistics.logical_blocks:
            if getattr(block, "type", "") == "paragraph":    
                # Flaga: wdowy
                widow_which =  getattr(block, "is_widow", 0)
                if widow_which > 0:    
                    error = self.handle_widow(block, widow_which)
                    if error:
                        converter_errors.append(error)
                # Flaga: bękarty
                bekart_which = getattr(block, "is_bekart", 0)
                if bekart_which != 0:
                    error = self.handle_bekart(block, bekart_which)
                    if error:
                        converter_errors.append(error)
                # Flaga: szewce
                szewc_which = getattr(block, "is_szewc", 0)
                if szewc_which != 0:
                    error = self.handle_szewc(block, szewc_which)
                    if error:
                        converter_errors.append(error)


        return converter_errors

    def check_widows(self):
        #TODO: przeniesc tu sprawdzanie wdów (musimy mieć opcje żeby nie robić zaawansowanej redakcji do trybu szybkiego)
        pass

    def handle_widow(self, block, widow_which):
        if not block.words:
            return

        widow_words = block.words[-widow_which:]
        first_word = widow_words[0]
        last_word = widow_words[-1]
        found_text = " ".join([w.text for w in widow_words])

        left_x = first_word.bbox[0]
        right_x = last_word.bbox[2]
        top_y = min([w.bbox[1] for w in widow_words])
        bottom_y = max([w.bbox[3] for w in widow_words])
        widow_bbox = (round(left_x, 2), round(top_y, 2), round(right_x, 2), round(bottom_y, 2))
        
        return Error(
            id=self._get_next_id(), 
            module=self.module,
            category="widow", 
            page_nr=last_word.page_number,
            bounding_box=widow_bbox, 
            text=found_text,
            comments="Wykryto wdowę"
        )
    
    def check_bekarts(self):
        #TODO: to samo co wyżej
        pass

    def handle_bekart(self, block, bekart_which):
        if not block.words:
            return

        bekart_words = block.words[-bekart_which:]
        first_word = bekart_words[0]
        last_word = bekart_words[-1]
        found_text = " ".join([w.text for w in bekart_words])

        left_x = first_word.bbox[0]
        right_x = last_word.bbox[2]
        top_y = min([w.bbox[1] for w in bekart_words])
        bottom_y = max([w.bbox[3] for w in bekart_words])
        bekart_bbox = (round(left_x, 2), round(top_y, 2), round(right_x, 2), round(bottom_y, 2))
        
        return Error(
            id=self._get_next_id(), 
            module=self.module,
            category="bekart", 
            page_nr=last_word.page_number,
            bounding_box=bekart_bbox, 
            text=found_text,
            comments="Wykryto bękarta"
        )
    
    def check_szewce(self):
        #TODO: to samo co wyżej
        pass

    def handle_szewc(self, block, szewc_which):
        if not block.words:
            return

        szewc_words = block.words[-szewc_which:]
        first_word = szewc_words[0]
        last_word = szewc_words[-1]
        found_text = " ".join([w.text for w in szewc_words])

        left_x = first_word.bbox[0]
        right_x = last_word.bbox[2]
        top_y = min([w.bbox[1] for w in szewc_words])
        bottom_y = max([w.bbox[3] for w in szewc_words])
        bekart_bbox = (round(left_x, 2), round(top_y, 2), round(right_x, 2), round(bottom_y, 2))
        
        return Error(
            id=self._get_next_id(), 
            module=self.module,
            category="szewc", 
            page_nr=first_word.page_number - 1,
            bounding_box=bekart_bbox, 
            text=found_text,
            comments="Wykryto szewc"
        )
    
    def check_toc(self):
        wrong_entries = []
        is_toc = True

        if self.document_data.toc == None:
            is_toc = False
            return None, is_toc

        for entry in self.document_data.toc.entries:
            expected_page = entry.page
            expected_title = " ".join(entry.title.lower().strip().rstrip('.').split())
            correct_page = False

            for page in self.document_data.pages:
                if page.number == expected_page:
                    page_full_text = ""
                    for block in page.text_blocks:
                        for line in block.lines:
                            line_text = " ".join([s.text for s in line.spans])
                            page_full_text += line_text + " "
                        
                    page_full_text = " ".join(page_full_text.lower().split())
                        
                    if expected_title in page_full_text:
                        correct_page = True
                        break
                
            if not correct_page:
                wrong_entries.append(entry)
                    
            return wrong_entries, is_toc
        
    def check_footers(self):
        lack_of_footers = []
        page_1_footer_bbox = None

        for page in self.document_data.pages:
            footer_block = None

            for block in page.text_blocks:
                if block.block_type == "footer":
                    footer_block = block
            if page.number == 1:
                if footer_block:
                    page_1_footer_bbox = footer_block.bbox
            else: 
                if not footer_block:
                    lack_of_footers.append(page.number)

        return page_1_footer_bbox, lack_of_footers
    
    #------------------config checks-----------------------
    #funckje w tym bloku zwracają True jeśli wszystko ok, False jeśli wykryto błąd
    def check_interline_spacing(self, doc_data: DocumentData) -> bool:
        line_spacing = doc_data.get_dominant_line_spacing()
        if line_spacing is None:
            logging.warning("Redaction: nie można określić interlinii")
            return True
        elif abs(line_spacing - self.config.interlinia) > 0.1: # dopuszczalna różnica 0.1
            self.errors.append(Error(
                id = self._get_next_id(),
                module = self.module,
                category = "config_file",
                page_nr = None,
                bounding_box = (0,0,0,0),
                text = None,
                comments = f"Używana interlinia ({line_spacing}) jest niezgodna z wymaganą interlinią ({self.config.interlinia})."
            ))
            return False
        else:
            return True
        
    def check_page_count(self, doc_data: DocumentData) -> bool:
        page_count = doc_data.get_page_count()
        if page_count < self.config.min_stron:
            self.errors.append(Error(
                id = self._get_next_id(),
                module = self.module,
                category = "config_file",
                page_nr = None,
                bounding_box = (0,0,0,0),
                text = None,
                comments = f"Dokument ma {page_count} stron, mniej niż minimalna liczba {self.config.min_stron}"
            ))
            return False
        elif page_count > self.config.max_stron:
            self.errors.append(Error(
                id = self._get_next_id(),
                module = self.module,
                category = "config_file",
                page_nr = None,
                bounding_box = (0,0,0,0),
                text = None,
                comments = f"Dokument ma {page_count} stron, więcej niż maksymalna liczba {self.config.min_stron}."
            ))
            return False
        else:
            return True
    
    def check_font_size(self, doc_data: DocumentData) -> bool:
        most_used_font_size = max(doc_data.get_font_size_usage(), key=doc_data.get_font_size_usage().get, default=None)
        if most_used_font_size is None:
            logging.warning("Redaction: nie można określić rozmiaru czcionki")
            return True
        elif abs(most_used_font_size - self.config.font_size) > 0.1: # dopuszczalna różnica 0.1
            self.errors.append(Error(
                id = self._get_next_id(),
                module = self.module,
                category = "config_file",
                page_nr = None,
                bounding_box = (0,0,0,0),
                text = None,
                comments = f"Używany rozmiar czcionki ({most_used_font_size}) jest niezgodny z wymaganym rozmiarem czcionki ({self.config.font_size})."
            ))
            return False
        else:
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
                        self.errors.append(Error(
                            id = self._get_next_id(),
                            module = self.module,
                            category = "config_file",
                            page_nr = page_num,
                            bounding_box = (0,0,0,0),
                            text = None,
                            comments = f"Oczekiwany większy margines po lewej stronie stronie: left={margin.get('left', 0)}, right={margin.get('right', 0)}."
                        ))
                        return False
                else: # strona parzysta
                    if margin.get("right", 0) <= margin.get("left", 0):
                        self.errors.append(Error(
                            id = self._get_next_id(),
                            module = self.module,
                            category = "config_file",
                            page_nr = page_num,
                            bounding_box = (0,0,0,0),
                            text = None,
                            comments = f"Oczekiwany większy margines po prawej stronie stronie: left={margin.get('left', 0)}, right={margin.get('right', 0)}."
                        ))
                        return False
                    margins[page_num]["left"], margins[page_num]["right"] = margins[page_num]["right"], margins[page_num]["left"]
            
            org_margin = margins[1]
            for page_num, margin in margins.items():
                if margin != org_margin:
                    self.errors.append(Error(
                        id = self._get_next_id(),
                        module = self.module,
                        category = "config_file",
                        page_nr = page_num,
                        bounding_box = (0,0,0,0),
                        text = None,
                        comments = f"Margines na tej stronie różni się od marginesów na pozostałych stronach: {margin} vs {org_margin}."
                    ))
                    return False
            return True

    def check_format(self, doc_data: DocumentData) -> bool:
        tolerance = 10

        formats = {
            "a5": (420, 595),
            "a4": (595, 842),
            "a3": (842, 1191)
        }
        
        if self.config.format not in formats:
            logging.warning("Redaction: nieznany format strony w konfiguracji")
            return False
        exp_w,exp_h = formats[self.config.format]
        for page_num, (width,height) in doc_data.get_page_dimensions().items():
            if not ((abs(width - exp_w)<=tolerance and abs(height-exp_h)<=tolerance) or (abs(width-exp_h)<=tolerance and abs(height-exp_w)<=tolerance)):
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "config_file",
                    page_nr = page_num,
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = f"Używany format strony (wymiary: {width}x{height})jest niezgodny z wymaganiami {formats[self.config.format].upper()}"
                ))
                return False
            else:
                return True
    
    def check_orientation(self, doc_data: DocumentData) -> bool:
        doc_data.get_page_dimensions()
        for page_num, (width, height) in doc_data.get_page_dimensions().items():
            if self.config.orientation == "pionowa" and width > height:
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "config_file",
                    page_nr = page_num,
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = f"Orientacja strony ({width}x{height}) niezgodna z wymaganiami (pionowa)."
                ))
                return False
            elif self.config.orientation == "pozioma" and height > width:
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "config_file",
                    page_nr = page_num,
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = f"Orientacja strony ({width}x{height}) niezgodna z wymaganiami (pozioma)."
                ))
                return False
            else:
                return True

    def check_fonts(self, doc_data: DocumentData) -> bool:
        font_usage = doc_data.get_font_usage()
        if not font_usage:
            logging.warning("Redaction: nie można określić używanych czcionek")
            return True
        for font in font_usage.keys():
            if font not in self.config.font_list:
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "config_file",
                    page_nr = None,
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = f"Używana czcionka ({font}) jest niezgodna z wymaganą czcionką."   
                ))
                return False
        return True
    
    def check_justification(self, doc_data: DocumentData) -> bool:
        expected_justified = self.config.justowanie
        errors_found = False

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
                        self.errors.append(Error(
                            id = self._get_next_id(),
                            module = self.module,
                            category = "config_file",
                            page_nr = page.number,
                            bounding_box = line.bbox,
                            text = None,
                            comments = f"Wykryto brak justowania w akapicie (linia {i+1})"
                        ))
                        errors_found = True

                    elif not expected_justified and is_justified:
                        self.errors.append(Error(
                            id = self._get_next_id(),
                            module = self.module,
                            category = "config_file",
                            page_nr = page.number,
                            bounding_box = line.bbox,
                            text = None,
                            comments = f"Wykryto niepoprawne justowanie w akapicie (linia {i+1})"
                        ))
                        errors_found = True

        if not errors_found:
            logging.info("Redaction: justowanie zgodne z wymaganiami")

        return not errors_found