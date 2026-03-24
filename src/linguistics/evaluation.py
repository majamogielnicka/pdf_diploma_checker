import json
import os
from pathlib import PurePath

def normalize_word_idxs(item):
    """
    Extracts and normalizes word indexes from an error dictionary.

    Args:
        item (dict): Dictionary containing error information.

    Returns:
        tuple: Tuple of sorted, unique word indexes.
    """

    word_idxs = item.get("word_idxs", [])
    if not isinstance(word_idxs, list):
        return tuple()
    return tuple(sorted(set(word_idxs)))

def normalize_prediction(prediction_error):
    """
    Standardizes a prediction error to ensure all required evaluation keys exist.

    Args:
        prediction_error (dict): Dictionary containing error information.

    Returns:
        dict: Standardized error dictionary.
    """
    return {
        "category": prediction_error["category"],
        "word_idxs": normalize_word_idxs(prediction_error),
        "block_id": prediction_error["block_id"],
        "content": prediction_error.get("content", ""),
    }

def load_json(path):
    """
    Loads JSON data from the specified path.

    Args:
        path (str): Path to the JSON file.

    Returns:
        list: List of error dictionaries.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def exact_match(prediction_error, correct_error):
    """
    Checks if a predicted error matches the correct error perfectly.

    Args:
        prediction_error (dict): Dictionary containing predicted error information.
        correct_error (dict): Dictionary containing correct error information.

    Returns:
        bool: True if the errors match exactly, False otherwise.
    """
    return (
        prediction_error["category"] == correct_error["category"]
        and prediction_error["block_id"] == correct_error["block_id"]
        and prediction_error["word_idxs"] == normalize_word_idxs(correct_error)
    )

def evaluate(prediction_errors, correct_errors):
    """
    Evaluates predictions against gold standard errors and computes TP, FP, FN metrics.

    Args:
        prediction_errors (list): List of predicted error dictionaries.
        correct_errors (list): List of correct error dictionaries.

    Returns:
        tuple: Tuple containing TP, FP, and FN counts.
    """
    matcher = exact_match
    used_correct_errors = set()
    tp = 0
    fp = 0

    for prediction_error in prediction_errors:
        prediction_error_n = normalize_prediction(prediction_error)
        matched = False

        for idx, correct_error in enumerate(correct_errors):
            if idx in used_correct_errors:
                continue
            if matcher(prediction_error_n, correct_error):
                used_correct_errors.add(idx)
                tp += 1
                matched = True
                break

        if not matched:
            fp += 1

    fn = len(correct_errors) - len(used_correct_errors)
    return tp, fp, fn


def metrics(tp, fp, fn):
    """
    Calculates precision, recall, and F1 score from raw prediction counts.

    Args:
        tp (int): True positives count.
        fp (int): False positives count.
        fn (int): False negatives count.

    Returns:
        dict: Dictionary containing precision, recall, and F1 score.
    """
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}

if __name__ == "__main__":
    
    #temporary file for testing

    base_dir = PurePath(__file__).parent / "evaluation"
    mock_data_dir = base_dir / "mock_data"
    prediction_errors_dir = base_dir / "prediction_errors"
    expected_errors_dir = base_dir / "expected_errors"
    mock_data_files = []
    for file in os.listdir(mock_data_dir):
        if file.endswith(".json"):
            mock_data_files.append(file)
    results_path = base_dir / "results" / "evaluation_results.txt"
    os.makedirs(base_dir / "results", exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as out_file:
        for mock_data_file in mock_data_files:
            correct_errors = load_json(str(expected_errors_dir / f"expected_errors_from_{mock_data_file}"))
            prediction_errors = load_json(str(prediction_errors_dir / f"predictions_{mock_data_file}"))
            tp, fp, fn = evaluate(prediction_errors, correct_errors)
            m = metrics(tp, fp, fn)
            result_str = (
                f"Document: {mock_data_file}\n"
                f"TP={tp}, FP={fp}, FN={fn}\n"
                f"Precision={m['precision']:.4f}\n"
                f"Recall={m['recall']:.4f}\n"
                f"F1={m['f1']:.4f}\n"
                f"{'-' * 30}\n"
            )
            out_file.write(result_str)