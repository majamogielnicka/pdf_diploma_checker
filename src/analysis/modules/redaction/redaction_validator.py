'''
Znajduje się tu główna klasa RedactionValidator, która zajmuje się
...walidowaniem...
pdf'a pod względem błędów z redakcji i "zaawansowanej" redakcji.

'''

from analysis.extraction.bare_struct import DocumentData, TocData, TofData, TotData
from analysis.extraction.converter_linguistics_clean import get_acronym_pages
from analysis.extraction.schema import FinalDocument
from common.errors.error_struct import Error, FileError, Module
from dataclasses import dataclass
from typing import List
import json
import logging
import re

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
        lang = getattr(self, "language", "pl")
        try:
            self.interlinia = float(data["interlinia"])
            self.min_stron = int(data["minimalna_liczba_stron"])
            self.max_stron = int(data["maksymalna_liczba_stron"])
            self.font_size = int(data["rozmiar_czcionki"])
            
            if self.min_stron > self.max_stron:
                if lang == "en":
                    raise FileError("min_pages > max_pages, config error")
                else: 
                    raise FileError("min_stron > max_stron, błąd konfiguracji")

            if data["margines"].lower() not in ["lustrzany", "standardowy"]:
                if lang == "en":
                    raise FileError("Incorrect margin, expected 'lustrzany' (mirror) or 'standardowy' (standard)")
                else:
                    raise FileError("błędny margines, oczekiwano 'lustrzany' lub 'standardowy'")
            self.margin_type = data["margines"]


            if data["format"].lower() not in ["a3", "a4", "a5"]:
                if lang == "en":
                    raise FileError("Incorrect page format, expected 'a3', 'a4' or 'a5'")
                else:
                    raise FileError("błędny format strony, oczekiwano 'a3', 'a4' lub 'a5'")
            self.format = data["format"]

            if data["orientacja"].lower() not in ["pionowa", "pozioma"]:
                if lang == "en":
                    raise FileError("Incorrect orientation, expected 'pionowa' (vertical) or 'pozioma' (horizontal)")
                else:
                    raise FileError("błędna orientacja, oczekiwano 'pionowa' lub 'pozioma'")
            self.orientation = data["orientacja"]

            if data["justowanie"].lower() not in ["tak", "nie"]:
                if lang == "en":
                    raise FileError("Incorrect justification, expected 'tak' (yes) or 'nie' (no)")
                else:
                    raise FileError("błędne justowanie, oczekiwano 'tak' lub 'nie'")
            self.justowanie = data["justowanie"].lower() == "tak"

            czcionki_dict = data.get("czcionka", {})
            self.font_list = list(czcionki_dict.values())
            
            if not self.font_list:
                if lang == "en":
                    logging.warning("Allowed fonts are not provided in the configuration file")
                else:
                    logging.warning("brak dozwolonych czcionek w konfiguracji")

        except KeyError as e:
            if lang == "en":
                raise FileError(f"Lacking key in the configuration file: {e}")
            else:
                raise FileError(f"brakujący klucz w konfiguracji: {e}")
        except ValueError as e:
            if lang == "en":
                raise FileError(f"Incorrect data type in the configuration file: {e}")
            else:
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
        self.errors.clear() 
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
            self.check_footers()
            self.check_toc()
            self.check_tof()
            self.check_tot()
            self.check_raster_images()

            self.check_list_order()

        #--------------------advanced redaction check
        if advanced_redaction_check:
            self.check_orphans()
            self.check_widows()
            self.check_bekarts()
            self.check_szewce()
            self.check_bibliography()
            #self.check_korytarze()
            self.check_bibliography_summary()
            self.check_caption_sources()

        self.remove_errors_from_toc_tof_tot()
        self.remove_errors_from_images()
        self.remove_errors_from_tables()
        self.remove_errors_from_acronyms_symbols()
        self.remove_errors_from_title_page()
        self.replace_global_errors()

        return self.errors
    
    def last_errors_to_json(self):
        return json.dumps([error.__dict__ for error in self.errors], ensure_ascii=False, indent=4)
    
    def last_errors_to_file(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.last_errors_to_json())

    def replace_global_errors(self):
        for page in self.document_data.pages:
            errors_on_page = []
            for error in self.errors:
                if error.bounding_box == (0,0,0,0):
                    if error.page_number == page.number or (page.number ==1 and error.page_number is None):
                        errors_on_page.append(error)

            num_errors = len(errors_on_page)
            if num_errors > 0:
                slot_width = page.width/num_errors

                for i, error in enumerate(errors_on_page):
                    new_x1 = i*slot_width + 5
                    new_x2 = (i+1)*slot_width-5
                    error.bounding_box = (round(new_x1, 2), 5, round(new_x2, 2), 45)

    def remove_errors_from_title_page(self):
        for error in self.errors[:]:
            if error.page_number == 0:
                self.errors.remove(error)

    def remove_errors_from_toc_tof_tot(self):
        if self.document_data.toc and self.document_data.toc.page_nums:
            toc_pages = self.document_data.toc.page_nums
        else:
            toc_pages = []

        if self.document_data.tof and self.document_data.tof.page_nums:
            tof_pages = self.document_data.tof.page_nums
        else:
            tof_pages = []

        if self.document_data.tot and self.document_data.tot.page_nums:
            tot_pages = self.document_data.tot.page_nums
        else:
            tot_pages = []

        errors_excluded = ["orphan", "corridor", "widow", "shoe_maker", "justification"]
        errors_fixed = []
        for error in self.errors:
            is_in_toc = error.page_number in toc_pages
            is_in_tof = error.page_number in tof_pages
            is_in_tot = error.page_number in tot_pages
            is_exluded = error.category in errors_excluded

            if (is_in_toc or is_in_tof or is_in_tot) and is_exluded:
                continue

            errors_fixed.append(error)
        self.errors = errors_fixed

    def remove_errors_from_images(self):
        def is_inside(error_bbox, image_bbox):
            return (
                error_bbox[0] >= image_bbox[0] - 10 and
                error_bbox[1] >= image_bbox[1] - 10 and
                error_bbox[2] <= image_bbox[2] + 10 and
                error_bbox[3] <= image_bbox[3] + 10
            )

        errors_excluded = ["orphan", "corridor", "widow", "shoe_maker", "justification"]
        filtered_errors = []

        for error in self.errors:
            error_to_remove = False

            if error.category in errors_excluded:
                for page in self.document_data.pages:
                    if error.page_number == page.number:
                        for image in page.images:
                            if is_inside(error.bounding_box, image.bbox):
                                error_to_remove = True
                                break
                        break 
            
            if not error_to_remove:
                filtered_errors.append(error)

        self.errors = filtered_errors
                                
    def remove_errors_from_tables(self):
        def is_inside(error_bbox, table_bbox):
            return (
                error_bbox[0] >= table_bbox[0] - 10 and
                error_bbox[1] >= table_bbox[1] - 10 and
                error_bbox[2] <= table_bbox[2] + 10 and
                error_bbox[3] <= table_bbox[3] + 10
            )

        errors_excluded = ["orphan", "corridor", "widow", "shoe_maker", "justification"]
        filtered_errors = []

        for error in self.errors:
            error_to_remove = False

            if error.category in errors_excluded:
                for page in self.document_data.pages:
                    if error.page_number == page.number:
                        for table in page.tables:
                            if is_inside(error.bounding_box, table.bbox):
                                error_to_remove = True
                                break
                        break 
            
            if not error_to_remove:
                filtered_errors.append(error)

        self.errors = filtered_errors

    def remove_errors_from_acronyms_symbols(self):
        from analysis.extraction.converter_linguistics_clean import PDFMapper, get_acronym_pages

        mapper = PDFMapper()
        linguistics_doc = mapper.map_to_schema(self.document_data)

        pages = get_acronym_pages(linguistics_doc) if linguistics_doc else []
        if pages is None:
            pages = []

        errors_excluded = ["orphan", "corridor", "widow", "shoe_maker", "justification"]
        errors_fixed = []
        for error in self.errors:
            is_in_acronyms = error.page_number in pages
            is_exluded = error.category in errors_excluded

            if is_in_acronyms and is_exluded:
                continue

            errors_fixed.append(error)
        self.errors = errors_fixed

    def check_orphans(self):
        '''This function checks every line in the document for orphans.'''
        orphans = []
        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Orphan detected - Conjunction at the end of the line."
        else:
            comment = "Wykryto sierotę - spójnik na końcu linii."
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

                        rect = (last_span.bbox[2] + 3, last_span.bbox[1] + 1, page.width - 1, last_span.bbox[3] - 1) #tested
                        if self.document_data.is_rect_intersecting(rect, page) != []:
                            continue

                        orphans.append(last_span)
                        self.errors.append(Error(
                            id = self._get_next_id(),
                            module = self.module,
                            category = "orphan",
                            page_number = page.number,
                            bounding_box = last_span.bbox,
                            text = last_span.text,
                            comments = comment
                        ))
        return orphans
    
    def check_korytarze(self):
        korytarze = []
        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Corridor detected - overlapping white gaps between words in neighbouring lines."
        else: 
            comment = "Wykryto korytarz - nakładające się przerwy między wyrazami w sąsiednich liniach."
        for page in self.document_data.pages:
            if page.number < 3:
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
                                    category = "corridor",
                                    page_number = page.number,
                                    bounding_box = (x1, span.bbox[1] - 15, x2, span.bbox[3]),
                                    text = None,
                                    comments = comment
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
        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Blank page detected."
        else: 
            comment = "Wykryto pustą stronę."

        for page in self.document_data.pages:
            if page.is_blank == True:
                blank_pages.append(page)
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "blank_page",
                    page_number = page.number,
                    bounding_box = (0,0,0,0),
                    text = "",
                    comments = comment
                ))

        return blank_pages
    
    def check_raster_images(self):
        """
        Checking whether image type is raster (image_type == 'raster').
        """
        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Raster image detected - it is recommended to use vector images. Consider changing an image format"
        else: 
            comment = "Wykryto grafikę rastrową - zaleca się stosowanie grafik wektorowych. Rozważ zmianę formatu grafiki."

        for page in self.document_data.pages:
            for img in page.images:
                if getattr(img, "image_type", "") == "raster":
                    
                    self.errors.append(Error(
                        id=self._get_next_id(),
                        module=self.module,
                        category="raster_image",
                        page_number=page.number,
                        bounding_box=img.bbox, 
                        text=img.description,   
                        comments=comment
                    ))
          
    def check_bibliography(self):   
        """
        Iterates through the logical blocks to identify words flagged with 
        incorrect or missing bibliography references. It generates and appends 
        an Error object for each flagged instance.
        """     
        for block in self.document_data_linguistics.logical_blocks:
            words = getattr(block, "words", [])
            for word in words:
                if getattr(word, "incorrect_bibliography", 0) == 1:        
                    error = self._handle_bibliography(word)
                    if error:
                        self.errors.append(error)

    def _handle_bibliography(self, word):
        """
        Constructs an Error object for an invalid or missing bibliography reference.

        Args:
            word (WordInfo): The word object containing the invalid citation and its metadata.

        Returns:
            Error: A formatted error object detailing the citation mismatch.
        """
        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Incorrect bibliography reference detected - element is not included in bibliography section or does not exist."
        else: 
            comment = "Wykryto niepoprawne odwołanie do bibliografii - element nie występuje w spisie bibliografii lub ten nie istnieje."

        return Error(
            id=self._get_next_id(), 
            module=self.module,
            category="incorrect bibiography refference", 
            page_number=word.page_number,
            bounding_box=word.bbox, 
            text=word.text,
            comments=comment
        )

    def check_widows(self):
        """
        Scans all paragraph blocks for 'widow' flags (a very short line left at the 
        end of a paragraph). If detected, it processes and logs the corresponding error.
        """
        for block in self.document_data_linguistics.logical_blocks:
            if getattr(block, "type", "") == "paragraph":    
                # Flaga: wdowy
                widow_which =  getattr(block, "is_widow", 0)
                if widow_which > 0:    
                    error = self._handle_widow(block, widow_which)
                    if error:
                        self.errors.append(error)

    def check_bibliography_summary(self):
        """
        Compiles a complete list of all recognized bibliography entries from the 
        document and appends them as a single, informational summary Error object 
        for easy review.
        """
        bib_entries = []
        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Summary: List of all items detected in the bibliography."
        else: 
            comment = "Podsumowanie: Lista wszystkich pozycji wykrytych w spisie bibliograficznym."

        for block in self.document_data_linguistics.logical_blocks:
            if getattr(block, "is_bibliography", False) and hasattr(block, "items"):
                for item in block.items:
                    text_content = item.text.strip()
                    if text_content:
                        marker = item.words[0].text if item.words else ""
                        bib_entries.append(f"{marker} {text_content}\n")
                        
                        #bib_entries.append(text_content)

        if bib_entries:
            summary_text = "\n".join(bib_entries)
            
            summary_error = Error(
                id=self._get_next_id(),
                module=self.module,
                category="bibliography_summary",
                page_number=3,  
                bounding_box=(0, 0, 0, 0),  
                text=summary_text,
                comments=comment
            )
            self.errors.append(summary_error)
                
    def _handle_widow(self, block, widow_which):
        """
        Calculates the precise bounding box for the isolated words constituting 
        a 'widow' and constructs the corresponding Error object.

        Args:
            block (ParagraphBlock): The paragraph block containing the widow.
            widow_which (int): The number of words that make up the widow at the end of the block.

        Returns:
            Error: A formatted error object representing the typographical widow.
        """

        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Widow detected - very short line left at end of a paragraph."
        else: 
            comment = "Wykryto wdowę - bardzo krótki wiersz pozostawiony na końcu akapitu."

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
            page_number=last_word.page_number,
            bounding_box=widow_bbox, 
            text=found_text,
            comments=comment
        )
    
    def check_bekarts(self):
        """
        Scans all paragraph blocks for 'bastard' flags (the last line of a paragraph 
        isolated at the top of the following page). If detected, it processes and 
        logs the corresponding error.
        """
        for block in self.document_data_linguistics.logical_blocks:
            if getattr(block, "type", "") == "paragraph":
                # Flaga: bękarty
                bekart_which = getattr(block, "is_bekart", 0)
                if bekart_which != 0:
                    error = self._handle_bekart(block, bekart_which)
                    if error:
                        self.errors.append(error)

    def _handle_bekart(self, block, bekart_which):
        """
        Calculates the precise bounding box for the isolated words constituting 
        a 'bastard' and constructs the corresponding Error object.

        Args:
            block (ParagraphBlock): The paragraph block containing the bastard.
            bekart_which (int): The number of words that make up the bastard on the new page.

        Returns:
            Error: A formatted error object representing the typographical bastard.
        """

        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Bastard detected - last line of a paragraph left on the next page"
        else: 
            comment = "Wykryto bękarta - ostatni wiersz akapitu pozostawiony na kolejnej stronie."

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
            category="bastard", 
            page_number=last_word.page_number,
            bounding_box=bekart_bbox, 
            text=found_text,
            comments=comment
        )
    
    def check_szewce(self):
        """
        Scans all paragraph blocks for 'shoemaker' flags (the first line of a new 
        paragraph isolated at the bottom of the previous page). If detected, it 
        processes and logs the corresponding error.
        """
        for block in self.document_data_linguistics.logical_blocks:
            if getattr(block, "type", "") == "paragraph":
                # Flaga: szewce
                szewc_which = getattr(block, "is_szewc", 0)
                if szewc_which != 0:
                    error = self._handle_szewc(block, szewc_which)
                    if error:
                        self.errors.append(error)

    def _handle_szewc(self, block, szewc_which):
        """
        Calculates the precise bounding box for the isolated words constituting 
        a 'shoemaker' and constructs the corresponding Error object.

        Args:
            block (ParagraphBlock): The paragraph block containing the shoemaker.
            szewc_which (int): The number of words that make up the shoemaker at the beginning of the block.

        Returns:
            Error: A formatted error object representing the typographical shoemaker.
        """

        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Shoemaker detected - first line of paragraph left on the previous page."
        else: 
            comment = "Wykryto szewca - pierwszy wiersz akapitu pozostawiony na poprzedniej stronie."


        if not block.words:
            return

        szewc_words = block.words[:szewc_which]
        first_word = szewc_words[0]
        last_word = szewc_words[-1]
        found_text = " ".join([w.text for w in szewc_words])

        left_x = first_word.bbox[0]
        right_x = last_word.bbox[2]
        top_y = min([w.bbox[1] for w in szewc_words])
        bottom_y = max([w.bbox[3] for w in szewc_words])
        szewc_bbox = (round(left_x, 2), round(top_y, 2), round(right_x, 2), round(bottom_y, 2))
        
        return Error(
            id=self._get_next_id(), 
            module=self.module,
            category="shoemaker", 
            page_number=first_word.page_number,
            bounding_box=szewc_bbox, 
            text=found_text,
            comments=comment
        )
    
    def check_caption_sources(self):
        """
        Iterates through the text blocks acting as visual captions to verify if they 
        lack proper source attributions or bibliography citations. Calculates the 
        bounding box of the flagged caption and appends a corresponding Error object.
        """

        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "The caption does not contain a reference to the bibliography (e.g. [1]) or information about the source (e.g. 'Source: ...')."
        else: 
            comment = "Podpis nie zawiera odwołania do bibliografii (np. [1]) ani informacji o źródle (np. 'Źródło: opracowanie własne')."

        for block in self.document_data_linguistics.logical_blocks:
            if getattr(block, "incorrect_caption", 0) == 1:
                
                if getattr(block, "words", []):
                    left_x = min(w.bbox[0] for w in block.words)
                    top_y = min(w.bbox[1] for w in block.words)
                    right_x = max(w.bbox[2] for w in block.words)
                    bottom_y = max(w.bbox[3] for w in block.words)
                    caption_bbox = (round(left_x, 2), round(top_y, 2), round(right_x, 2), round(bottom_y, 2))
                    page_num = block.words[0].page_number
                else:
                    caption_bbox = (0, 0, 0, 0)
                    page_num = 1

                self.errors.append(Error(
                    id=self._get_next_id(),
                    module=self.module,
                    category="missing_caption_source",
                    page_number=page_num,
                    bounding_box=caption_bbox,
                    text=getattr(block, "content", ""),
                    comments=comment
                ))

        if lang == "en":
            comment = "The figure does not have a valid source or bibliography reference in its caption."
        else: 
            comment = "Rysunek nie posiada poprawnego źródła lub odwołania do bibliografii w swoim podpisie."

        for visual in self.document_data_linguistics.floating_elements.visual_elements:
            if getattr(visual, "incorrect_caption", 0) == 1:
                
                caption_dict = getattr(visual, "caption", {})
                caption_text = caption_dict.get("text", "") if isinstance(caption_dict, dict) else ""
                
                self.errors.append(Error(
                    id=self._get_next_id(),
                    module=self.module,
                    category="missing_caption_source",
                    page_number=getattr(visual, "page_number", 1),
                    bounding_box=getattr(visual, "bbox", (0, 0, 0, 0)),
                    text=caption_text,
                    comments=comment
                ))
    
    def check_toc(self):
        wrong_entries = []
        is_toc = True
        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = "Missing table of contents detected"
        else: 
            comment = "Wykryto brak spisu treści."

        if self.document_data.toc == None:
            error = Error(
                id = self._get_next_id(),
                module=self.module,
                category = "lack_of_TOC",
                page_number = 1,
                bounding_box = (0,0,0,0), 
                text = None,
                comments = comment
            )
            self.errors.append(error)
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
            if lang == "en":
                comment = f"Chapter/Subchapter '{entry.title}' is not on the specified page (page {entry.page})."
            else: 
                comment = f"Rozdział/Podrozdział '{entry.title}' nie znajduje się na wskazanej stronie (strona {entry.page})."
    
            if not correct_page:
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "TOC_mismatch",
                    page_number = entry.src_page,
                    bounding_box = entry.bbox,
                    text = entry.title,
                    comments = comment
                ))
                wrong_entries.append(entry)

        return wrong_entries, is_toc
    
    def check_tot(self):
        wrong_entries = []
        lang = getattr(self, "language", "pl")

        if lang == "en":
            comment = "Missing table list detected."
        else: 
            comment = "Wykryto brak spisu tabel."
    
        if self.document_data.tot == None:
            error = Error(
                id = self._get_next_id(),
                module=self.module,
                category = "lack_of_TOT",
                page_number = 1,
                bounding_box = (0,0,0,0), 
                text = None,
                comments = comment
            )
            self.errors.append(error)
            return 

        for entry in self.document_data.tot.entries:
            expected_title = " ".join(entry.title.lower().strip().rstrip('.').split())
            correct_page = False

            for page in self.document_data.pages:
                if page.number == entry.page:
                    for table in page.tables:
                        if not table.description:
                            continue
                        table_desc = " ".join(table.description.lower().strip().split())
                        
                        if expected_title in table_desc or table_desc in expected_title:
                            correct_page = True
                            break

                if correct_page: 
                    break

            if lang == "en":
                comment = f"The table titled '{entry.title}' is not on the specified page (page {entry.page})."
            else: 
                comment = f"Tabela o tytule '{entry.title}' nie znajduje się na wskazanej stronie (strona {entry.page})."
    
            if not correct_page:
                self.errors.append(Error(
                    id=self._get_next_id(),
                    module=self.module,
                    category="TOT_mismatch",
                    page_number=entry.src_page,
                    bounding_box=entry.bbox,
                    text=entry.title,
                    comments=comment
                ))
                wrong_entries.append(entry)

        return wrong_entries

    def check_tof(self):
        wrong_entries = []
        lang = getattr(self, "language", "pl")

        if lang == "en":
            comment = "Missing list of figures detected."
        else: 
            comment = "Wykryto brak spisu rysunków."
    
        if self.document_data.tof == None:
            error = Error(
                id = self._get_next_id(),
                module=self.module,
                category = "lack_of_TOF",
                page_number = 1,
                bounding_box = (0,0,0,0), 
                text = None,
                comments = comment
            )
            self.errors.append(error)
            is_toc = False
            return None, is_toc

        for entry in self.document_data.tof.entries:
            expected_title = " ".join(entry.title.lower().strip().rstrip('.').split())
            correct_page = False

            for page in self.document_data.pages:
                if page.number == entry.page:
                    for image in page.images:
                        if not image.description:
                            continue
                            
                        image_desc = " ".join(image.description.lower().strip().split())
                        
                        if expected_title in image_desc or image_desc in expected_title:
                            correct_page = True
                            break
                if correct_page: 
                    break
            if lang == "en":
                comment = f"The figure titled '{entry.title}' is not on the specified page (Page {entry.page})."
            else: 
                comment = f"Rysunek o tytule '{entry.title}' nie znajduje się na wskazanej stronie (Strona {entry.page})."
    
            if not correct_page:
                self.errors.append(Error(
                    id=self._get_next_id(),
                    module=self.module,
                    category="TOF_mismatch",
                    page_number=entry.src_page,
                    bounding_box=entry.bbox,
                    text=entry.title,
                    comments= comment
                ))
                wrong_entries.append(entry)

        return wrong_entries
    
    def check_footers(self):
        first_chapter_page = None
        lang = getattr(self, "language", "pl")
        keywords = [
            "streszczenie", "abstract", "wstęp", "wstep", "introduction",
            "spis treści", "spis tresci", "table of contents", "table of content", "toc",
            "spis rysunków", "spis rysunkow", "list of figures", "tof",
            "spis tabel", "spis tablic", "list of tables", "tot",
            "wykaz skrótów", "wykaz skrotow", "list of abbreviations"
        ]

        font_sizes = []
        for page in self.document_data.pages:
            for block in page.text_blocks:
                for line in block.lines:
                    for span in line.spans:
                        if span.text and span.text.strip() and hasattr(span, "size"):
                            font_sizes.append(span.size)
        
        main_font_size = 12.0
        if font_sizes:
            font_sizes.sort()
            main_font_size = font_sizes[len(font_sizes) // 2]

        for page in self.document_data.pages:
            if page.number > 10:
                break

            line_counter = 0
            found_keyword = False
            
            for block in page.text_blocks:
                for line in block.lines:
                    line_text_lower = ""
                    max_span_size = 0.0
                    
                    for span in line.spans:
                        if span.text:
                            line_text_lower += span.text.lower() + " "
                            if hasattr(span, "size") and span.size > max_span_size:
                                max_span_size = span.size
                    
                    line_text_lower = line_text_lower.strip()
                    if not line_text_lower:
                        continue
                        
                    line_counter += 1
                    
                    if line_counter <= 4:
                        if max_span_size >= (main_font_size + 1.5):
                            if any(word == line_text_lower or line_text_lower.startswith(word) for word in keywords):
                                found_keyword = True
                                break
                if found_keyword:
                    break
            
            if found_keyword:
                if page.number > 0:
                    first_chapter_page = page.number
                    break

        if first_chapter_page is None and self.document_data.toc and self.document_data.toc.entries:
            first_chapter_page = self.document_data.toc.entries[0].page

        for page in self.document_data.pages:
            footer_block = None

            for block in page.text_blocks:
                if block.block_type == "footer":
                    footer_block = block
                    
            if first_chapter_page is not None and page.number < first_chapter_page:
                if footer_block:
                    if lang == "en":
                        comment = f"Numbering detected on page{page.number}, which comes before the first chapter or heading (expected from page {first_chapter_page})."
                    else: 
                        comment = f"Wykryto numerację na stronie {page.number}, która znajduje się przed pierwszym rozdziałem lub nagłówkiem (oczekiwano od strony {first_chapter_page})."
    
                    self.errors.append(Error(
                        id = self._get_next_id(),
                        module = self.module,
                        category = "Footer_on_forbidden_page",
                        page_number = page.number,
                        bounding_box = footer_block.bbox, 
                        text = "Footer detected",
                        comments = comment
                    ))
            else: 
                if footer_block is None:
                    if lang == "en":
                        comment = f"Missing page numbering detected on page {page.number}"
                    else: 
                        comment = f"Wykryto brak numeracji na stronie {page.number}" 
    
                    self.errors.append(Error(
                        id = self._get_next_id(),
                        module = self.module,
                        category = "No_footer",
                        page_number = page.number,
                        bounding_box = (self.document_data.pages[page.number].width/2 - 20, 
                                        self.document_data.pages[page.number].height - 60, 
                                        self.document_data.pages[page.number].width/2 + 20, 
                                        self.document_data.pages[page.number].height - 30),
                        text = None,
                        comments = comment  
                    ))                 
                else:
                    raw_text = " ".join([" ".join([s.text for s in l.spans]) for l in footer_block.lines])
                    match = re.search(r"(\d+)", raw_text)

                    if match:
                        detected_num = int(match.group(1))
                        if detected_num != page.number:
                            if lang == "en":
                                comment = f"Invalid page number. Detected: {detected_num}, expected: {page.number}."
                            else: 
                                comment = f"Błędny numer strony. Wykryto: {detected_num}, oczekiwano: {page.number}."
    
                            self.errors.append(Error(
                                id=self._get_next_id(),
                                module=self.module,
                                category="Wrong_page_number",
                                page_number=page.number,
                                bounding_box=footer_block.bbox,
                                text=raw_text,
                                comments=comment
                            ))

        is_ftr_error = False
        for error in self.errors:
            if error.category == "No_footer" or error.category == "Wrong_page_number":
                is_ftr_error = True
        if is_ftr_error:
            if lang == "en":
                comment = "Due to incorrect page numbering, it is impossible to check the correctness of the table of contents, figures and tables."
            else: 
                comment = "Z racji niepoprawnej numeracji stron, niemożliwe jest sprawdzenie poprawności spisu treści, rysunków oraz tabel."
    
            self.errors.append(Error(
                id = self._get_next_id(),
                module = self.module,
                category = "numeration_invalid",
                page_number = 1,
                bounding_box = (0,0,0,0), 
                text = None,
                comments = comment
            ))
        return None
    #------------------config checks-----------------------
    def check_interline_spacing(self, doc_data: DocumentData) -> bool:
        line_spacing = doc_data.get_dominant_line_spacing()
        lang = getattr(self, "language", "pl")
        if lang == "en":
            comment = f"The line spacing used ({line_spacing}) does not match the required line spacing ({self.config.line_spacing})."
        else: 
            comment = f"Używana interlinia ({line_spacing}) jest niezgodna z wymaganą interlinią ({self.config.interlinia})."

        
        if line_spacing is None:
            if lang == "en":
                logging.warning("Redaction: cannot specify line spacing")
            else: 
                logging.warning("Redaction: nie można określić interlinii")
            return True
        elif abs(line_spacing - self.config.interlinia) > 0.1:

            self.errors.append(Error(
                id = self._get_next_id(),
                module = self.module,
                category = "config_file",
                page_number = None,
                bounding_box = (0,0,0,0),
                text = None,
                comments = comment
            ))
            return False
        else:
            return True
        
    def check_page_count(self, doc_data: DocumentData) -> bool:
        page_count = doc_data.get_page_count()
        lang = getattr(self, "language", "pl")

        if lang == "en":
            comment = f"The document has {page_count} pages, less than the minimum number of {self.config.min_pages}"
        else: 
            comment = f"Dokument ma {page_count} stron, mniej niż minimalna liczba {self.config.min_stron}"

        if page_count < self.config.min_stron:
            self.errors.append(Error(
                id = self._get_next_id(),
                module = self.module,
                category = "config_file",
                page_number = None,
                bounding_box = (0,0,0,0),
                text = None,
                comments = comment
            ))
            return False
        elif page_count > self.config.max_stron:
            if lang == "en":
                comment = f"The document has {page_count} pages, more than the maximum number of {self.config.max_pages}."
            else: 
                comment = f"Dokument ma {page_count} stron, więcej niż maksymalna liczba {self.config.max_stron}."

            self.errors.append(Error(
                id = self._get_next_id(),
                module = self.module,
                category = "config_file",
                page_number = None,
                bounding_box = (0,0,0,0),
                text = None,
                comments = comment
            ))
            return False
        else:
            return True
    
    def check_font_size(self, doc_data: DocumentData) -> bool:
        most_used_font_size = max(doc_data.get_font_size_usage(), key=doc_data.get_font_size_usage().get, default=None)
        lang = getattr(self, "language", "pl")
        if most_used_font_size is None:
            if lang == "en":
                logging.warning("Redaction: Unable to determine font size.")
            else: 
                logging.warning("Redaction: nie można określić rozmiaru czcionki.")
            return True
        elif abs(most_used_font_size - self.config.font_size) > 0.1: 
            if lang == "en":
                comment = f"The font size used ({most_used_font_size}) does not match the required font size ({self.config.font_size})."
            else: 
                comment = f"Używany rozmiar czcionki ({most_used_font_size}) jest niezgodny z wymaganym rozmiarem czcionki ({self.config.font_size})."
            self.errors.append(Error(
                id = self._get_next_id(),
                module = self.module,
                category = "config_file",
                page_number = None,
                bounding_box = (0,0,0,0),
                text = None,
                comments = comment
            ))
            return False
        else:
            return True

    def check_margins(self, doc_data: DocumentData) -> bool:
        margins = doc_data.get_margins()
        lang = getattr(self, "language", "pl")
        if not margins:
            if lang == "en":
                logging.warning("Redaction: Cannot determine margins")
            else:
                logging.warning("Redaction: nie można określić marginesów")
            return True
        if self.config.margin_type == "lustrzany":
            if len(margins) < 2:
                if lang == "en":
                    logging.warning("Redaction: too few pages to evaluate mirror margins")
                else:
                    logging.warning("Redaction: zbyt mało stron do oceny marginesów lustrzanych")
                return True

            for page_num, margin in margins.items():
                if page_num % 2 == 1: 
                    if lang == "en":
                        comment = f"Expected larger margin on the left side of the page: left={margin.get('left', 0)}, right={margin.get('right', 0)}."
                    else:
                        comment = f"Oczekiwany większy margines po lewej stronie stronie: left={margin.get('left', 0)}, right={margin.get('right', 0)}."
                    if margin.get("left", 0) <= margin.get("right", 0):
                        self.errors.append(Error(
                            id = self._get_next_id(),
                            module = self.module,
                            category = "config_file",
                            page_number = page_num,
                            bounding_box = (0,0,0,0),
                            text = None,
                            comments = comment
                        ))
                        return False
                else: 
                    if lang == "en":
                        comment = f"Expected larger margin on the right side of the page: left={margin.get('left', 0)}, right={margin.get('right', 0)}."
                    else:
                        comment = f"Oczekiwany większy margines po prawej stronie stronie: left={margin.get('left', 0)}, right={margin.get('right', 0)}."
                    if margin.get("right", 0) <= margin.get("left", 0):
                        self.errors.append(Error(
                            id = self._get_next_id(),
                            module = self.module,
                            category = "config_file",
                            page_number = page_num,
                            bounding_box = (0,0,0,0),
                            text = None,
                            comments = comment
                        ))
                        return False
                    margins[page_num]["left"], margins[page_num]["right"] = margins[page_num]["right"], margins[page_num]["left"]
            
            org_margin = margins[1]
            for page_num, margin in margins.items():
                if margin != org_margin:
                    if lang == "en":
                        comment = f"The margin on this page is different from the margins on other pages: {margin} vs {org_margin}."
                    else:
                        comment = f"Margines na tej stronie różni się od marginesów na pozostałych stronach: {margin} vs {org_margin}."
                    self.errors.append(Error(
                        id = self._get_next_id(),
                        module = self.module,
                        category = "config_file",
                        page_number = page_num,
                        bounding_box = (0,0,0,0),
                        text = None,
                        comments = comment
                    ))
                    return False
            return True

    def check_format(self, doc_data: DocumentData) -> bool:
        tolerance = 10
        lang = getattr(self, "language", "pl") 

        formats = {
            "a5": (420, 595),
            "a4": (595, 842),
            "a3": (842, 1191)
        }
        
        if self.config.format not in formats:
            if lang == "en":
                logging.warning("Redaction: unknown page format in the configuration file")
            else:
                logging.warning("Redaction: nieznany format strony w konfiguracji")

            return False
        exp_w,exp_h = formats[self.config.format]
        for page_num, (width,height) in doc_data.get_page_dimensions().items():
            if lang == "en":
                comment = f"The page format used (dimensions: {width}x{height}) does not comply with the requirements of {formats[self.config.format].upper()}"
            else:
                comment = f"Używany format strony (wymiary: {width}x{height})jest niezgodny z wymaganiami {formats[self.config.format].upper()}"

            if not ((abs(width - exp_w)<=tolerance and abs(height-exp_h)<=tolerance) or (abs(width-exp_h)<=tolerance and abs(height-exp_w)<=tolerance)):
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "config_file",
                    page_number = page_num,
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = comment
                ))
                return False
            else:
                return True
    
    def check_orientation(self, doc_data: DocumentData) -> bool:
        doc_data.get_page_dimensions()
        lang = getattr(self, "language", "pl") 
        for page_num, (width, height) in doc_data.get_page_dimensions().items():
            if self.config.orientation == "pionowa" and width > height:
                if lang == "en":
                    comment = f"Page orientation ({width}x{height}) does not meet requirements (vertical)."
                else:
                    comment = f"Orientacja strony ({width}x{height}) niezgodna z wymaganiami (pionowa)."

                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "config_file",
                    page_number = page_num,
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = comment
                ))
                return False
            elif self.config.orientation == "pozioma" and height > width:
                if lang == "en":
                    comment = f"Page orientation ({width}x{height}) does not meet requirements (horizontal)."
                else:
                    comment = f"Orientacja strony ({width}x{height}) niezgodna z wymaganiami (pozioma)."

                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "config_file",
                    page_number = page_num,
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = comment
                ))
                return False
            else:
                return True

    def check_fonts(self, doc_data: DocumentData) -> bool:
        font_usage = doc_data.get_font_usage()
        lang = getattr(self, "language", "pl")
        if not font_usage:
            if lang == "en":
                logging.warning("Redaction: Unable to determine used fonts")
            else:    
                logging.warning("Redaction: nie można określić używanych czcionek")
            return True
        for font in font_usage.keys():
            if font not in self.config.font_list:
                if lang == "en":
                    comment = f"The font used ({font}) does not match the required font."
                else:
                    comment = f"Używana czcionka ({font}) jest niezgodna z wymaganą czcionką."  
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "config_file",
                    page_number = None,
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = comment
                ))
                return False
        return True
    
    def check_justification(self, doc_data: DocumentData) -> bool:
        expected_justified = self.config.justowanie
        errors_found = False
        lang = getattr(self, "language", "pl") 

        for page in doc_data.pages:
            for block in page.text_blocks:
                if self.is_paragraph(block):
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
                            if lang == "en":
                                comment = f"Lack of justification detected in the paragraph (line {i+1})"
                            else:
                                comment = f"Wykryto brak justowania w akapicie (linia {i+1})"
                            self.errors.append(Error(
                                id = self._get_next_id(),
                                module = self.module,
                                category = "justification",
                                page_number = page.number,
                                bounding_box = line.bbox,
                                text = None,
                                comments = comment
                            ))
                            errors_found = True

                        elif not expected_justified and is_justified:
                            if lang == "en":
                                comment = f"Incorrect justification detected in the paragraph (line {i+1})"
                            else:
                                comment = f"Wykryto niepoprawne justowanie w akapicie (linia {i+1})"
                            self.errors.append(Error(
                                id = self._get_next_id(),
                                module = self.module,
                                category = "justification",
                                page_number = page.number,
                                bounding_box = line.bbox,
                                text = None,
                                comments = comment
                            ))
                            errors_found = True

        if not errors_found:
            if lang == "en":
                logging.info("Redaction: Justification as required")
            else:
                logging.info("Redaction: justowanie zgodne z wymaganiami")
            
        return not errors_found
    

    def check_list_order(self):
        lang = getattr(self, "language", "pl") 
        if self.document_data.toc and self.document_data.toc.entries:
            error_found_toc = False
            entries_toc = self.document_data.toc.entries
            
            for i in range(1, len(entries_toc)):
                current_entry_toc = entries_toc[i]
                previous_entry_toc = entries_toc[i - 1]

                if current_entry_toc.page < previous_entry_toc.page:
                    error_found_toc = True
                    break

            if error_found_toc:   
                if lang == "en":
                    comment = "Descending numbering in the table of contents has been detected. Subsequent table of contents entries should be arranged in non-descending order relative to the page number they appear on."
                else:
                    comment = "Wykryto malejącą numerację w spisie treści. Kolejne wpisy spisu treści powinny zostać ustawione niemalejąco względem numeru strony, na którym się znajdują."
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "toc_order_error",
                    page_number = self.document_data.toc.page_nums[0],
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = comment
                ))


        if self.document_data.tof and self.document_data.tof.entries:
            error_found_tof = False
            entries_tof = self.document_data.tof.entries
            
            for i in range(1, len(entries_tof)):
                current_entry_tof = entries_tof[i]
                previous_entry_tof = entries_tof[i - 1]

                if current_entry_tof.page < previous_entry_tof.page:
                    error_found_tof = True
                    break

            if error_found_tof:  
                if lang == "en":
                    comment = "Descending numbering has been detected in the figure list. Subsequent figure list entries should be set non-descendingly relative to the page number they appear on."
                else:
                    comment = "Wykryto malejącą numerację w spisie figur. Kolejne wpisy spisu figur powinny zostać ustawione niemalejąco względem numeru strony, na którym się znajdują."
   
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "tof_order_error",
                    page_number = self.document_data.tof.page_nums[0],
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = comment
                ))
                
        if self.document_data.tot and self.document_data.tot.entries:
            error_found_tot = False
            entries_tot = self.document_data.tot.entries
            
            for i in range(1, len(entries_tot)):
                current_entry_tot = entries_tot[i]
                previous_entry_tot = entries_tot[i - 1]

                if current_entry_tot.page < previous_entry_tot.page:
                    error_found_tot = True
                    break

            if error_found_tot:  
                if lang == "en":
                    comment = "Descending numbering has been detected in the table list. Subsequent table list entries should be set non-descendingly relative to the page number they appear on."
                else:
                    comment = "Wykryto malejącą numerację w spisie tabel. Kolejne wpisy spisu tabel powinny zostać ustawione niemalejąco względem numeru strony, na którym się znajdują."
     
                self.errors.append(Error(
                    id = self._get_next_id(),
                    module = self.module,
                    category = "tot_order_error",
                    page_number = self.document_data.tot.page_nums[0],
                    bounding_box = (0,0,0,0),
                    text = None,
                    comments = comment
                ))
        return 
    
    def is_paragraph(self, block):
        """
        Funkcja sprawdzająca, czy bloki to paragraph
        """
        block_type = getattr(block, "type", "")
        if block_type is None:
            block_type = ""
            
        block_type_lower = block_type.lower()
        types = ["paragraph"]
        
        if any(i_type in block_type_lower for i_type in types):
            return True
            
        return False