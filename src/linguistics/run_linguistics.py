from language_error_extractor import *
from decimal_point_extractor import decimal_check
from exeptions_check import *
from list_check import check_coherence_in_list
from pathlib import PurePath
import json

#starting point to run all linguistucs functions made so far.
if __name__ == "__main__":
    #for tests, waiting on json with pdf language
    text_path = PurePath(__file__).parent / 'tests' / 'test_3.txt'
    json_path = PurePath(__file__).parent / 'tests' / 'test.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        document = json.load(f)
    if text_path.name.endswith("1.txt"):
        text_language = "pl"
    elif text_path.name.endswith("3.txt"):
        text_language = "en"
    else: text_language = "pl"
    text = extract_text(text_path)
    language_matches = language_tool_analisys(text_language, text)
    list_matches = check_coherence_in_list(document, text_language)
    checked_exeptions = check_exeptions(language_matches, text, text_language)
    decimal_matches = decimal_check(text_language, text)
    matches = checked_exeptions + decimal_matches + list_matches
    extract_errors_to_json(matches)