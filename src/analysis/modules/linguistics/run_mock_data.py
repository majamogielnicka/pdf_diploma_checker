from .language_error_extractor import *
from .decimal_point_extractor import decimal_check
from .dash_check import dash_check
from .exeptions_check import *
from .list_check import check_coherence_in_list
from .sentence_check import *
from .proper_names import get_proper_names
from .helpers import extract_errors_to_json
from .first_definition import check_first_definition
from pathlib import PurePath
from typing import Dict, Any
import dataclasses
from src.analysis.extraction.extraction_json import extractPDF
from src.analysis.extraction.converter_linguistics import PDFMapper
from pathlib import Path, PurePath
import os

if __name__ == "__main__":
    pdf_file = Path(__file__).parent / "doro.pdf"
    
    document = extractPDF(str(pdf_file))
    blocks = PDFMapper.map_to_schema(document)
    acronyms_with_definitions = check_first_definition(blocks)
    text_language = 'pl'
    proper_names = get_proper_names(blocks, text_language)
    decimal_matches, decimal_counter = decimal_check(text_language, blocks)
    dash_matches, dash_counter = dash_check(text_language, blocks)
    language_matches, whitespace_counter = language_tool_analisys(text_language, blocks)
    list_matches = check_coherence_in_list(blocks, text_language, proper_names, acronyms_with_definitions)
    checked_exeptions = check_exeptions(language_matches, blocks, text_language, proper_names)
    language_style_matches, sentence_analisys = sentence_check(blocks, text_language)
    matches = checked_exeptions + decimal_matches + list_matches + language_style_matches + dash_matches
    print(f"Znaleziono błędów: {len(matches)}")
    extract_errors_to_json(matches)
