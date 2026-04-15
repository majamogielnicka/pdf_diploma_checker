from .language_error_extractor import *
from .decimal_point_extractor import decimal_check
from .dash_check import dash_check
from .exeptions_check import *
from .list_check import check_coherence_in_list
from .sentence_check import *
from .proper_names import get_proper_names
from .helpers import extract_errors_to_json, get_context
from .first_definition import check_first_definition
from .check_acronym import check_if_was_defined
from pathlib import PurePath
from src.analysis.extraction.extraction_json import extractPDF
from src.analysis.extraction.converter_linguistics import PDFMapper
from pathlib import Path, PurePath
import os

def run_linguistics(raw_blocks):
    text_language = 'pl'
    blocks = get_context(raw_blocks)
    extract_errors_to_json(blocks, "final_document2.json")
    proper_names = get_proper_names(raw_blocks, text_language)
    acronyms_with_definitions = check_first_definition(raw_blocks, proper_names)
    acronym_matches = check_if_was_defined(raw_blocks, acronyms_with_definitions)
    decimal_matches, decimal_counter = decimal_check(blocks)
    dash_matches, dash_counter = dash_check(blocks)
    language_matches, whitespace_counter = language_tool_analisys(blocks)
    list_matches = check_coherence_in_list(raw_blocks, text_language, proper_names, acronyms_with_definitions)
    checked_exeptions = check_exeptions(language_matches, blocks, proper_names)
    language_style_matches, sentence_analisys = sentence_check(blocks)
    matches = checked_exeptions + decimal_matches + list_matches + acronym_matches + language_style_matches + dash_matches
    return matches


if __name__ == "__main__":
    pdf_file = "data/zusz.pdf"
    document = extractPDF(str(pdf_file))
    raw_blocks = PDFMapper.map_to_schema(document)
    matches = run_linguistics(raw_blocks)
    # print(f"Znaleziono błędów: {len(matches)}")
    extract_errors_to_json(matches, "errors2.json")
