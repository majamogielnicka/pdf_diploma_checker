'''
Znajduje się tu główna klasa RedactionValidator, która zajmuje się
...walidowaniem...
pdf'a pod względem błędów z redakcji i "zaawansowanej" redakcji.

'''

from src.analysis.extraction.bare_struct import DocumentData
from src.common.errors.error_struct import RedactionError, Module

class RedactionValidator:
    def __init__(self, document_data: DocumentData, document_data_linguistics: DocumentData):
        self.document_data = document_data
        self.document_data_linguistics = document_data_linguistics
        self.module = Module.REDACTION
        self.id_counter = 0

    def _get_next_id(self):
        id = f"ERR_RED_{self.id_counter}"
        self.id_counter += 1
        return id

    def validate(self):
        errors = []
        orphans = self.check_orphans()
        for orphan in orphans:
            error = RedactionError(
                id=self._get_next_id(),
                module=self.module,
                category="orphan",
                page_nr=0, #orphan.page_nr,
                bounding_box= 0, #orphan.bounding_box,
                text=orphan.text,
                comments="Orphan character detected. Consider checking the redaction quality."
            )
            errors.append(error)
        blank_pages = self.check_blank_page()
        for blank_page in blank_pages:
            error = RedactionError(
                id = self._get_next_id(),
                module = self.module,
                category = "blank_page",
                page_nr = blank_page.number,
                bounding_box = None,
                text = None,
                comments = "Blank page detected. Consider checking content of this page."
            )
            errors.append(error)
        wrong_toc_entries, is_toc = self.check_toc()

        if not is_toc:
            error = RedactionError(
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
                error = RedactionError(
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
            error = RedactionError(
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
            error = RedactionError(
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
        return errors

    def check_orphans(self):
        orphans = []
        conjuncions = []
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
                        if last_span.text in ".,;:!?\"')]}":
                            continue
                        orphans.append(last_span)
        return orphans
    
    def check_blank_page(self):
        blank_pages = []
        for page in self.document_data.pages:
            if page.is_blank == True:
                blank_pages.append(page)

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
        
        return RedactionError(
            id=self._get_next_id(), 
            module=self.module,
            category="widow", 
            page_nr=last_word.page_number,
            bounding_box=widow_bbox, 
            text=found_text,
            comments="Wykryto wdowę"
        )
    
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
        
        return RedactionError(
            id=self._get_next_id(), 
            module=self.module,
            category="bekart", 
            page_nr=last_word.page_number,
            bounding_box=bekart_bbox, 
            text=found_text,
            comments="Wykryto bękarta"
        )
    
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
        
        return RedactionError(
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




