import language_tool_python
from lingua import Language, LanguageDetectorBuilder
import os
import json
from linguistics_types import Error_type
from decimal_point_extractor import decimal_check
import dataclasses

def extract_text(text_path: str) -> str:
    """
    Reads text from a file.
    
    Args:
        text_path (str): The path to the text file to be read.
    
    Returns:
        Text from a file extracted to a string.
    """

    for obj in os.listdir(os.path.join(os.path.dirname(__file__), "json")):
        os.remove(os.path.join(os.path.dirname(__file__), "json", obj))

    with open(text_path, encoding='utf-8') as file:
        text = file.read()

    return text


def language_tool_analisys(text_language: str, text: str) -> list:
    
    """
    Performs an initial grammar and spelling check in the specified language. Detects double spaces, some dashes and interpunction errors.
    
    Args:
        text_language (str): The language in which the text is written ("en" for English, "pl" for Polish).
        text (str): The string of text to be analysed.
    
    Returns:
        list: A list of matches.
    """

    if text_language == "en":
        tool_en = language_tool_python.LanguageTool('en-GB')
        matches = tool_en.check(text)

    elif text_language == "pl":
        tool_pl = language_tool_python.LanguageTool('pl-PL')
        matches = tool_pl.check(text)
    
    languages = [Language.ENGLISH, Language.POLISH]
    detector = LanguageDetectorBuilder.from_languages(*languages).build()
    tool_en = language_tool_python.LanguageTool('en-GB')
    new_matches = []
    for match in matches:
        if match.category == "TYPOS":
            sentence = match.sentence
            word = text[match.offset:match.offset + match.error_length]
            language = detector.detect_language_of(word)
            if language == Language.ENGLISH and text_language == "pl":
                en_matches = tool_en.check(word)
                for en_match in en_matches:
                    en_match.sentence = sentence
                new_matches.extend(en_matches)
                continue
            else:
                new_matches.append(match)
        else:
            new_matches.append(match)

    return new_matches


def extract_errors_to_json(matches: list) -> None:

    """
    Extracts errors from the list of matches and writes them to a JSON file.
    
    Args:
        matches (list): A list of errors to be extracted.

    Returns:
        None    
    """
    num = 0
    for match in matches:
        num += 1  

        x = Error_type(
            category= match.category,
            message= match.message,
            offset = match.offset,
            error_length = match.error_length
        )
        x_serialized = dataclasses.asdict(x)
        f = open(os.path.join(os.path.dirname(__file__), "json",f"error_file_{num}.json"), "w", encoding="utf-8")
        json.dump(x_serialized, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    text_path = os.path.join(os.path.dirname(__file__),'tests', 'test_2.txt')
    if text_path.endswith("1.txt"):
        text_language = "pl"
    elif text_path.endswith("3.txt"):
        text_language = "en"
    else: text_language = "pl"
    text = extract_text(text_path)
    language_matches = language_tool_analisys(text_language, text)
    decimal_matches = decimal_check(text_language, text)
    matches = language_matches + decimal_matches
    extract_errors_to_json(matches)



