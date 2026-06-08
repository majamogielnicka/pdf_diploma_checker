"""Compute thesis-related grading signals based on summaries and purpose alignment."""

import sys
import os
import time

_src_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for _p in (os.path.dirname(_src_dir), _src_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common.path import resource_path

from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text

from analysis.modules.llm.get_purpose import get_purpose
from analysis.modules.llm.get_subtitles import get_subtitles
from analysis.modules.llm.get_summary import get_summaries
from analysis.modules.llm.similarity import compute_similarity_for_summaries
from analysis.modules.llm.goal_realization import get_purpose_grade
from analysis.modules.llm.config import EMBEDDING_MODEL, THESIS_PATH, LANGUAGE


threshold = 0.785


def calculate_embedding_grade(purpose, summaries):
    """Compute an embedding-based grade and per-section off-topic flags."""

    similarity_result = compute_similarity_for_summaries(
        purpose=purpose,
        summaries=summaries,
        embedding_model=EMBEDDING_MODEL,
    )

    items = similarity_result.get("items", [])
    total_sections = len(items)

    if total_sections == 0:
        return {
            "grade": 0.0,
            "max_grade": 100.0,
            "s_emb": 0.0,
            "threshold": threshold,
            "total_sections": 0,
            "off_topic_sections": 0,
            "p_off": 100.0,
            "items": [],
        }

    off_topic_sections = 0

    for item in items:
        cosine_similarity = float(item.get("cosine_similarity", 0.0))
        below_threshold = cosine_similarity < threshold
        item["below_threshold"] = below_threshold

        if below_threshold:
            off_topic_sections += 1

    p_off = (off_topic_sections / total_sections) * 100.0
    s_emb = 100.0 - p_off
    grade = s_emb

    return {
        "grade": round(grade, 2),
        "max_grade": 100.0,
        "s_emb": s_emb,
        "threshold": threshold,
        "total_sections": total_sections,
        "off_topic_sections": off_topic_sections,
        "p_off": p_off,
        "items": items,
    }


def get_content_grade(purpose, summaries):
    """Return overall embedding grade and labels of off-topic sections."""

    embedding_result = calculate_embedding_grade(
        purpose=purpose,
        summaries=summaries
    )
    
    grade = embedding_result.get("grade", 0.0)
    items = embedding_result.get("items", [])
    
    # Extract off-topic heading labels (items below threshold)
    off_topic_headings = [
        (
            item.get("display")
            or item.get("heading")
            or item.get("title")
            or item.get("subtitle")
            or f"Section {idx + 1}"
        )
        for idx, item in enumerate(items)
        if item.get("below_threshold", False)
    ]
    
    # Return (grade, off_topic_heading_labels)
    return (grade, off_topic_headings)

def get_overall_grade(purpose_grade, embedding_grade, sota_grade):
    """Combine partial scores into the final weighted grade."""

    overall_grade = 0.2* sota_grade + 0.2 * purpose_grade + 0.6 * embedding_grade 
    return overall_grade


def main():
    """Run the full grading pipeline for the configured thesis PDF."""

    pdf_path = THESIS_PATH
    language = LANGUAGE

    print(f"PDF_PATH: {pdf_path}")
    print(f"PDF_EXISTS: {pdf_path.exists()}")
    print(f"PDF_ABSOLUTE: {pdf_path.resolve()}")

    if not pdf_path.exists():
        print(f"Error: file does not exist: {pdf_path}")
        return

    raw_doc = extractPDF_llm(str(pdf_path.resolve()))

    if raw_doc is None:
        print("Error: extractPDF_llm returned None.")
        return

    plain_text = get_plain_text(pdf_path)

    purpose = get_purpose(plain_text, LANGUAGE)

    subtitles = get_subtitles(raw_doc)
    summaries = get_summaries(subtitles, LANGUAGE)

    grade, off_topic_headings = get_content_grade(
        purpose=purpose,
        summaries=summaries
    )

    purpose_score, purpose_reason = get_purpose_grade(plain_text, purpose, LANGUAGE)

    print("THESIS PURPOSE:")
    print(purpose)
    print()
    print("EMBEDDING SCORE:")
    print(f"Score: {grade}")
    print(f"PURPOSE REALIZATION SCORE: {purpose_score} - {purpose_reason}")
    print(f"Off-topic headings indices: {off_topic_headings}")



if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    print(f"Program runtime: {end - start:.2f} s")