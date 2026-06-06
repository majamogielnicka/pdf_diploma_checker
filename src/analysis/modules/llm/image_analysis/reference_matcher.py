import re

class ReferenceMatcher:
    def find_references(self, paragraphs, image_id):
        '''
        wejscie: paragraphs (lista stringów z tekstem) oraz image_id (identyfikator rysunku).
        wyjscie: lista stringów zawierająca wyłącznie akapity odnoszące się do danego obrazka.
        opis: Wyszukuje w tekście odwołania do konkretnego rysunku za pomocą wyrażeń regularnych.
        '''
        matched_paragraphs = []
        
        safe_image_id = re.escape(str(image_id))

        pattern = re.compile(rf"(?i)rys(?:unek|\.)?\s*{safe_image_id}(?!\.?\d)")

        for para in paragraphs:
            if pattern.search(para):
                matched_paragraphs.append(para)

        return matched_paragraphs