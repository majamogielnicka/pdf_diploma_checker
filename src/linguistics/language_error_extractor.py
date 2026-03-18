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
                    en_match.offset += match.offset
                new_matches.extend(en_matches)
                continue
            else:
                new_matches.append(match)
        else:
            new_matches.append(match)
    errors = []
    for new_match in new_matches:
        error = Error_type(
            content = text[new_match.offset:new_match.offset + new_match.error_length],
            category= new_match.category,
            message= new_match.message,
            offset = new_match.offset,
            error_length = new_match.error_length
        )
        errors.append(error)
    return errors


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
        match_serialized = dataclasses.asdict(match)
        f = open(os.path.join(os.path.dirname(__file__), "json",f"error_file_{num}.json"), "w", encoding="utf-8")
        json.dump(match_serialized, f, ensure_ascii=False, indent=4)





