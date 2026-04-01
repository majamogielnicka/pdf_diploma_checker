from src.linguistics.language_error_extractor import *
from src.linguistics.decimal_point_extractor import decimal_check
from src.linguistics.dash_check import dash_check
from src.linguistics.exeptions_check import *
from src.linguistics.list_check import check_coherence_in_list
from src.linguistics.sentence_check import *
from src.linguistics.proper_names import get_proper_names
from pathlib import PurePath
from src.redaction.schema import FinalDocument, ParagraphBlock, ListBlock, WordInfo, HeadingInfo, ListItem
from typing import Dict, Any
import dataclasses
import os
import json

def to_json(document, file_path):

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(asdict(document), f, ensure_ascii=False, indent=4)

def from_dict(data):

    """
        Changes dict to FinalDocument object

        Args:
            data (dict): Dictionary to convert

        Returns:
            FinalDocument: FinalDocument object
    """
    metadata = data["metadata"]
    logical_blocks = []
    for block_data in data["logical_blocks"]:
        b_type = block_data["type"]
        if b_type == "paragraph":
            words = [WordInfo(**w) for w in block_data["words"]]
            headings = [HeadingInfo(**h) for h in block_data["headings"]]
            logical_blocks.append(ParagraphBlock(
                block_id=block_data["block_id"],
                content=block_data["content"],
                words=words,
                headings=headings,
                type=b_type
            ))
        elif b_type == "list":
            items = []
            for item_data in block_data["items"]:
                words = [WordInfo(**w) for w in item_data["words"]]
                items.append(ListItem(
                    item_id=item_data["item_id"],
                    marker_type=item_data["marker_type"],
                    text=item_data["text"],
                    bbox=item_data["bbox"],
                    words=words
                ))
            words = [WordInfo(**w) for w in block_data["words"]]
            logical_blocks.append(ListBlock(
                block_id=block_data["block_id"],
                content=block_data["content"],
                words=words,
                items=items,
                bbox=block_data["bbox"],
                type=b_type
            ))
    return FinalDocument(metadata=metadata, logical_blocks=logical_blocks)

if __name__ == "__main__":

    #temporary file
    eval_dir = PurePath(__file__).parent / "evaluation" 
    mock_data_dir = eval_dir / "mock_data"
    prediction_errors_dir = eval_dir / "prediction_errors"
    os.makedirs(prediction_errors_dir, exist_ok=True)
    file_num = 0
    for file in os.listdir(mock_data_dir):
        if file.endswith(".json"):
            json_path = mock_data_dir / file
            with open(json_path, 'r', encoding='utf-8') as f:
                document = json.load(f)
            text_language = 'en' if file.endswith('en.json') else 'pl'
            blocks = from_dict(document)
            proper_names = get_proper_names(blocks, text_language)
            decimal_matches, decimal_counter = decimal_check(text_language, blocks)
            dash_matches, dash_counter = dash_check(text_language, blocks)
            language_matches, whitespace_counter = language_tool_analisys(text_language, blocks)
            list_matches = check_coherence_in_list(blocks, text_language)
            checked_exeptions = check_exeptions(language_matches, blocks, text_language, proper_names)
            language_style_matches, sentence_analisys = sentence_check(blocks, text_language)
            matches = checked_exeptions + decimal_matches + list_matches + language_style_matches
            output_path = prediction_errors_dir / f'predictions_{file}'
            dict_matches = []
            checked_categories = {'PUNCTUATION', 'LIST_COHERENCE', 'DECIMAL', 'TYPOGRAPHY', 'PERSONAL_FORM'}
            for match in matches:
                if match.category in checked_categories:
                    m_dict = dataclasses.asdict(match)
                    dict_matches.append(m_dict)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dict_matches, f, ensure_ascii=False, indent=4)
            decimal_correct = [65, 66, 64, 51, 60]
            dash_correct = [68, 61, 67, 64, 58]
            whitespace_correct = [148, 149, 0, 0, 0]
            print(f"Document: {file}")
            print(f"Decimal counter: {decimal_counter} from {decimal_correct[file_num]}")
            print(f"Whitespace counter: {whitespace_counter} from {whitespace_correct[file_num]}")
            print(f"Dash counter: {dash_counter} from {dash_correct[file_num]}")
            file_num += 1
