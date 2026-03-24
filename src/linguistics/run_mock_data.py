from language_error_extractor import *
from decimal_point_extractor import decimal_check
from exeptions_check import *
from list_check import check_coherence_in_list
from pathlib import PurePath
from src.redaction.schema import FinalDocument
from proper_names import get_proper_names
import dataclasses
import os
import json

if __name__ == "__main__":

    #temporary file for testing
    eval_dir = PurePath(__file__).parent / "evaluation" 
    mock_data_dir = eval_dir / "mock_data"
    prediction_errors_dir = eval_dir / "prediction_errors"
    for file in os.listdir(mock_data_dir):
        if file.endswith(".json"):
            json_path = mock_data_dir / file
            with open(json_path, 'r', encoding='utf-8') as f:
                document = json.load(f)
            text_language = 'en' if file.endswith('en.json') else 'pl'
            blocks = FinalDocument.from_dict(document)
            decimal_matches = decimal_check(text_language, blocks)
            language_matches = language_tool_analisys(text_language, blocks)
            list_matches = check_coherence_in_list(blocks, text_language)
            checked_exeptions = check_exeptions(language_matches, blocks, text_language)
            matches = checked_exeptions + decimal_matches + list_matches
            output_path = prediction_errors_dir / f'predictions_{file}'
            dict_matches = []
            for match in matches:
                m_dict = dataclasses.asdict(match)
                dict_matches.append(m_dict)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dict_matches, f, ensure_ascii=False, indent=4)