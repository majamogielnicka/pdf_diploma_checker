"""Compute similarity between thesis purpose and section summaries."""

import sys
import os
from pathlib import Path
from datetime import datetime

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch

_src_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for _p in (os.path.dirname(_src_dir), _src_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common.path import resource_path

from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm
from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text

from analysis.modules.llm.get_subtitles import extract_subtitles_from_pdf
from analysis.modules.llm.get_purpose import get_purpose
from analysis.modules.llm.get_summary import summarize_subtitles
from analysis.modules.llm.config import EMBEDDING_MODEL, THESIS_PATH, OUTPUT_DIR, LANGUAGE, N_GPU_LAYERS


def normalize_text(text):
    """Normalize whitespace and non-breaking spaces in text."""

    if not text:
        return ""
    return " ".join(str(text).replace("\xa0", " ").split()).strip()


def get_purpose_text_for_embedding(text):
    """Format the purpose text as an embedding query."""

    text = normalize_text(text)
    return f"search_query: {text}"


def get_summary_text_for_embedding(text):
    """Format a summary text as an embedding document."""

    text = normalize_text(text)
    return f"search_document: {text}"


def compute_similarity_for_summaries(purpose, summaries, embedding_model=EMBEDDING_MODEL):
    """Return cosine similarities between purpose and all summary items."""

    purpose = normalize_text(purpose)
    items = []

    for item in summaries or []:
        new_item = dict(item)
        new_item["summary"] = normalize_text(new_item.get("summary") or "")
        items.append(new_item)

    if not purpose:
        for item in items:
            item["cosine_similarity"] = 0.0
        return {
            "purpose": purpose,
            "items": items,
            "average_similarity": 0.0,
        }

    texts = []
    valid_indices = []

    for i, item in enumerate(items):
        summary = item["summary"]
        if summary:
            valid_indices.append(i)
            texts.append(get_summary_text_for_embedding(summary))

    if not texts:
        for item in items:
            item["cosine_similarity"] = 0.0
        return {
            "purpose": purpose,
            "items": items,
            "average_similarity": 0.0,
        }

    use_cuda = (N_GPU_LAYERS != 0) and torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"

    model = SentenceTransformer(
        embedding_model,
        trust_remote_code=True,
        device=device,
    )

    purpose_embedding = model.encode(
        [get_purpose_text_for_embedding(purpose)],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    text_embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    scores = cosine_similarity(purpose_embedding, text_embeddings).flatten()

    for item in items:
        item["cosine_similarity"] = 0.0

    for idx, score in zip(valid_indices, scores):
        items[idx]["cosine_similarity"] = float(score)

    average_similarity = float(scores.mean()) if len(scores) > 0 else 0.0

    return {
        "purpose": purpose,
        "items": items,
        "average_similarity": average_similarity,
    }


def save_similarity_txt(pdf_path, result):
    """Write similarity results to a plain-text report file."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{Path(pdf_path).stem}_similarity.txt"

    lines = []
    lines.append(f"File: {Path(pdf_path).resolve()}")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("")
    lines.append("AVERAGE COSINE SIMILARITY")
    lines.append(f"{result.get('average_similarity', 0.0):.6f}")
    lines.append("")
    lines.append("THESIS PURPOSE")
    lines.append(result.get("purpose") or "None")
    lines.append("")
    lines.append("SIMILARITY FOR SUMMARIES")
    lines.append("")

    for item in result.get("items", []):
        lines.append(item.get("display") or "Section")
        lines.append("SUMMARY:")
        lines.append(item.get("summary") or "None")
        lines.append(f"COSINE_SIMILARITY: {item.get('cosine_similarity', 0.0):.6f}")
        lines.append("")
        lines.append("-" * 80)
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output_path


def main():
    """Run subtitle summarization similarity analysis for a thesis PDF."""

    pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else THESIS_PATH
    language = LANGUAGE

    if not pdf_path.exists():
        print(f"Error: file does not exist: {pdf_path}")
        return

    raw_doc = extractPDF_llm(str(pdf_path.resolve()))

    if raw_doc is None:
        print("Error: extractPDF_llm returned None.")
        return

    plain_text = get_plain_text(pdf_path)

    subtitles = extract_subtitles_from_pdf(raw_doc)
    purpose = get_purpose(plain_text, LANGUAGE)
    summaries = summarize_subtitles(raw_doc, subtitles, LANGUAGE)

    result = compute_similarity_for_summaries(purpose, summaries)
    output_path = save_similarity_txt(pdf_path, result)

    print(f"Result saved to: {output_path}")


if __name__ == "__main__":
    main()