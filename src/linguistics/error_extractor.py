import language_tool_python
from lingua import Language, LanguageDetectorBuilder
import os
import json

def extract_text(text_language: str, text_path: str) -> tuple[list, str]:

    """
    Reads text from a file and performs an initial grammar and spelling check in the specified language.
    
    Args:
        text_language (str): The language in which the text is written ("en" for English, "pl" for Polish).
        text_path (str): The path to the text file to be read.
    
    Returns:
        tuple[list, str]: A tuple containing the list of matches and the text content.
    """

    for obj in os.listdir(os.path.join(os.path.dirname(__file__), "json")):
        os.remove(os.path.join(os.path.dirname(__file__), "json", obj))

    with open(text_path, encoding='utf-8') as file:
        text = file.read()

    if text_language == "en":
        tool_en = language_tool_python.LanguageTool('en-GB')
        matches = tool_en.check(text)

    elif text_language == "pl":
        tool_pl = language_tool_python.LanguageTool('pl-PL')
        matches = tool_pl.check(text)
    
    return matches, text


def extract_errors_to_json(matches: list, text_language: str, text: str) -> None:

    """
    Extracts errors from the list of matches and writes them to a JSON file.
    
    Args:
        matches (list): A list of errors to be extracted.
        text_language (str): The language in which the text is written ("en" for English, "pl" for Polish).
        text (str): Text, which is being checked.

    Returns:
        None    
    """
    
    languages = [Language.ENGLISH, Language.POLISH]
    detector = LanguageDetectorBuilder.from_languages(*languages).build()
    tool_en = language_tool_python.LanguageTool('en-GB')
    num = 0
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

    for match in new_matches:
        num += 1  

        x = {
            "category": match.category,
            "rule_id": match.rule_id,
            "message": match.message,
            "replacements": match.replacements,
            "offset_in_context": match.offset_in_context,
            "context": match.context,
            "offset": match.offset,
            "error_length": match.error_length,
            "sentence": match.sentence,
            "rule_issue_type": match.rule_issue_type
        }
        
        f = open(os.path.join(os.path.dirname(__file__), "json",f"error_file_{num}.json"), "w", encoding="utf-8")
        json.dump(x, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":

   text_path = os.path.join(os.path.dirname(__file__),'tests', 'test_3.txt')
   if text_path.endswith("1.txt"):
       text_language = "pl"
   elif text_path.endswith("3.txt"):
       text_language = "en"
   matches, text = extract_text(text_language, text_path)
   extract_errors_to_json(matches, text_language, text)


