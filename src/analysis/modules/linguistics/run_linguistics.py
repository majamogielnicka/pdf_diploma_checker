'''
Plik powstał w celu ułatwienia uruchamiania modułu lingwistycznego z pipeline funkcją run_linguistics.
Dodatkowo uruchamiany jako main przeprowadza analizę bez udziału gui.
'''
from pathlib import Path
import sys

# _src = str(Path(__file__).resolve().parents[3])
# if _src not in sys.path:
#     sys.path.insert(0, _src)

from analysis.modules.linguistics.language_error_extractor import *
from analysis.modules.linguistics.decimal_point_extractor import decimal_check
from analysis.modules.linguistics.dash_check import dash_check
from analysis.modules.linguistics.exeptions_check import *
from analysis.modules.linguistics.list_check import check_coherence_in_list
from analysis.modules.linguistics.sentence_check import *
from analysis.modules.linguistics.proper_names import get_proper_names
from analysis.modules.linguistics.helpers import extract_errors_to_json, get_context
from analysis.modules.linguistics.first_definition import check_first_definition
from analysis.modules.linguistics.check_acronym import check_if_was_defined
from analysis.extraction.extraction_json import extractPDF
from analysis.modules.linguistics.bibliography_check import check_bibliography
from analysis.extraction.converter_linguistics_clean import PDFMapper
import json
from common.path import resource_path
import os

def remove_errors_inside_images(matches, raw_blocks):
    def is_inside(coord, image_bbox):
        return (
            coord[0] >= image_bbox[0] - 10 and
            coord[1] >= image_bbox[1] - 10 and
            coord[2] <= image_bbox[2] + 10 and
            coord[3] <= image_bbox[3] + 10
        )
    images = [ve for ve in raw_blocks.floating_elements.visual_elements if ve.type == "image"]
    if not images:
        return matches
    filtered = []
    for match in matches:
        inside = any(
            entry["coordinates"] != [0, 0, 0, 0] and
            any(
                ve.page_number == entry["page"] and is_inside(entry["coordinates"], ve.bbox)
                for ve in images
            )
            for entry in match.error_coordinate
        )
        if not inside:
            filtered.append(match)
    return filtered

def run_linguistics(raw_blocks, config_path=None):
    check_first_person = True
    check_bibtex = True
    if config_path:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data["sprawdzanie_formy_osobowej"].lower() not in ["tak", "nie"]:
                print("błędne sprawdzanie formy osobowej, oczekiwano 'tak' lub 'nie'")
            else:
                check_first_person = data["sprawdzanie_formy_osobowej"].lower() == "tak"
            if data["sprawdzanie_wg_bibtex"].lower() not in ["tak", "nie"]:
                print("błędne sprawdzanie bibtex, oczekiwano 'tak' lub 'nie'")
            else:
                check_bibtex = data["sprawdzanie_wg_bibtex"].lower() == "tak"
        except KeyError:
            print("Brak pola w konfiguracji lingwistyki.")
        except ValueError as e:
            print(f"niepoprawny typ danych w konfiguracji lingwistyki: {e}")
    blocks = get_context(raw_blocks)
    extracted_acronyms = raw_blocks.reference_sections.acronyms
    proper_names, bibliography_dict = get_proper_names(blocks)
    bib_matches = check_bibliography(blocks, raw_blocks.metadata["producer"], bibliography_dict, bibtex_check_bool = check_bibtex)
    acronyms_with_definitions, proper_names = check_first_definition(blocks, proper_names, extracted_acronyms)
    acronym_matches, proper_names = check_if_was_defined(blocks, acronyms_with_definitions, proper_names)
    decimal_matches, decimal_counter = decimal_check(blocks)
    dash_matches, dash_counter = dash_check(blocks)
    language_matches, whitespace_counter = language_tool_analisys(blocks)
    list_matches = check_coherence_in_list(blocks, proper_names, acronyms_with_definitions)
    main_font = raw_blocks.metadata.get("main_font")
    checked_exeptions = check_exeptions(language_matches, blocks, proper_names, main_font)
    language_style_matches, sentence_analisys = sentence_check(blocks, check_first_person=check_first_person, acronyms_with_definitions=acronyms_with_definitions)
    matches = checked_exeptions + decimal_matches + list_matches + acronym_matches + language_style_matches + dash_matches + bib_matches
    matches = remove_errors_inside_images(matches, raw_blocks)
    return matches, sentence_analisys

#plik pomocniczy do uruchamiania analizy bez GUI
if __name__ == "__main__":
    pdf_file = resource_path(os.path.join("analysis", "modules", "linguistics", "jabi.pdf"))
    try:
        document = extractPDF(str(pdf_file))
        mapper = PDFMapper()
        raw_blocks = mapper.map_to_schema(document)
        extracted_acronyms = raw_blocks.reference_sections.acronyms
    except AttributeError as e:
        print(f"Ekstrakcja zakończyła się niepowodzeniem.")
    else:
        matches = run_linguistics(raw_blocks)
