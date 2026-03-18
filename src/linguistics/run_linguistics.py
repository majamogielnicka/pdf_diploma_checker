from language_error_extractor import *
from decimal_point_extractor import decimal_check
from exeptions_check import *
from pathlib import PurePath

#starting point to run all linguistucs functions made so far.
if __name__ == "__main__":
    #for tests, waiting on json with pdf language
    text_path = PurePath(__file__).parent / 'tests' / 'test_3.txt'
    if text_path.endswith("1.txt"):
        text_language = "pl"
    elif text_path.endswith("3.txt"):
        text_language = "en"
    else: text_language = "pl"
    text = extract_text(text_path)
    language_matches = language_tool_analisys(text_language, text)
    checked_exeptions = check_exeptions(language_matches, text, text_language)
    decimal_matches = decimal_check(text_language, text)
    matches = checked_exeptions + decimal_matches
    extract_errors_to_json(matches)