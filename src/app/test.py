import os
import sys
import gc
import json
import time
import traceback
from pathlib import Path


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

SCRIPT_DIR = Path(__file__).resolve().parent

EXTRACTION_DIR = os.path.join(BASE_DIR, "analysis", "extraction")
COMMON_DIR = os.path.join(BASE_DIR, "common")
LINGUISTICS_DIR = os.path.join(BASE_DIR, "analysis", "modules", "linguistics")
LLM_DIR = os.path.join(BASE_DIR, "analysis", "modules", "llm")
REDACTION_DIR = os.path.join(BASE_DIR, "analysis", "modules", "redaction")

for path in [BASE_DIR, EXTRACTION_DIR, COMMON_DIR, LINGUISTICS_DIR, LLM_DIR, REDACTION_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)


# =========================
# STAŁE DO TESTU MAINEM
# =========================

THESIS_PATH = SCRIPT_DIR / "jost2.pdf"
LANGUAGE = "en"


def debug_print(title, value=None, verbose=True):
    if not verbose:
        return

    print()
    print(f"=== {title} ===", flush=True)

    if value is not None:
        if isinstance(value, (dict, list, tuple)):
            try:
                print(json.dumps(value, ensure_ascii=False, indent=2), flush=True)
            except Exception:
                print(value, flush=True)
        else:
            print(value, flush=True)

    print("=" * (len(title) + 8), flush=True)
    print()


def cleanup_text_llm_instances(verbose=False):
    try:
        from analysis.modules.llm import get_summary as _get_summary_mod
        from analysis.modules.llm import goal_realization as _goal_realization_mod
        from analysis.modules.llm import get_purpose as _get_purpose_mod

        llm_obj = getattr(_get_summary_mod, "_LLM", None)
        if llm_obj is not None:
            close_fn = getattr(llm_obj, "close", None)
            if callable(close_fn):
                close_fn()
            _get_summary_mod._LLM = None

        llm_obj = getattr(_goal_realization_mod, "_LLM", None)
        if llm_obj is not None:
            close_fn = getattr(llm_obj, "close", None)
            if callable(close_fn):
                close_fn()
            _goal_realization_mod._LLM = None

        model_cache = getattr(_get_purpose_mod, "_LLAMA_MODELS", None)
        if isinstance(model_cache, dict):
            for model in list(model_cache.values()):
                close_fn = getattr(model, "close", None)
                if callable(close_fn):
                    close_fn()
            model_cache.clear()

    except Exception as e:
        debug_print("CLEANUP ERROR", str(e), verbose)

    gc.collect()


def run_llm_module(doc_obj, pdf_path=None, language=None, verbose=False):
    """
    Moduł LLM do wywołania z pipeline.

    Zwraca:
        result, score, summary_text

    Czyli w pipeline:
        llm_result, content_grade_result, llm_summary_text = run_llm_module(...)
    """

    started = time.perf_counter()

    if pdf_path is None:
        pdf_path = THESIS_PATH

    if language is None:
        language = LANGUAGE

    pdf_path = str(pdf_path)

    debug_print("LLM MODULE START", {
        "pdf_path": pdf_path,
        "language": language,
    }, verbose)

    from analysis.extraction.extraction_json import get_raster_figure_numbers
    from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
    from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm

    from analysis.modules.llm.get_grade import get_overall_grade, get_content_grade
    from analysis.modules.llm.get_purpose import get_purpose
    from analysis.modules.llm.goal_realization import check_goal_realization, get_score_from_goal_result
    from analysis.modules.llm.get_summary import get_summaries
    from analysis.modules.llm.get_subtitles import get_subtitles
    from analysis.modules.llm.run_sota import get_final_sota_report
    from analysis.modules.llm.config import MODEL_PATH

    from analysis.modules.llm.image_analysis.run_image import analyze_images
    from analysis.modules.llm.image_analysis.image_quality_checker import get_full_image_quality_json
    from analysis.modules.llm.image_analysis.font_checker import get_font_consistency_report

    from analysis.extraction.converter_linguistics_clean import PDFMapper

    debug_print("MODEL", {
        "MODEL_PATH": str(MODEL_PATH),
        "MODEL_EXISTS": Path(MODEL_PATH).exists(),
    }, verbose)

    if not Path(MODEL_PATH).exists():
        raise FileNotFoundError(f"Model does not exist: {MODEL_PATH}")

    mapper = PDFMapper()

    debug_print("1. MAPPING DOC", "mapper.map_to_schema(doc_obj)", verbose)
    mapped_doc = mapper.map_to_schema(doc_obj)

    debug_print("2. GET PLAIN TEXT", "get_plain_text(pdf_path)", verbose)
    plain_txt_purpose = get_plain_text(pdf_path)
    debug_print("PLAIN TEXT LENGTH", len(plain_txt_purpose or ""), verbose)

    if not plain_txt_purpose:
        raise ValueError("plain_txt_purpose is empty")

    debug_print("3. EXTRACT PDF LLM", "extractPDF_llm(pdf_path)", verbose)
    txt_for_llm = extractPDF_llm(pdf_path)
    debug_print("TXT FOR LLM TYPE", type(txt_for_llm).__name__, verbose)

    if txt_for_llm is None:
        raise ValueError("extractPDF_llm returned None")

    debug_print("4. GET PURPOSE", "get_purpose(plain_txt_purpose, language)", verbose)
    purpose = get_purpose(plain_txt_purpose, language)
    debug_print("PURPOSE", purpose, verbose)

    if not purpose:
        raise ValueError("purpose is empty")

    debug_print("5. CHECK GOAL REALIZATION", "check_goal_realization(...)", verbose)
    goal_result = check_goal_realization(
        text=plain_txt_purpose,
        purpose=purpose,
        language=language,
    )

    debug_print("GOAL RESULT", goal_result, verbose)

    purpose_score = get_score_from_goal_result(goal_result)
    purpose_reason = str(goal_result.get("reason", "") or "")

    debug_print("PURPOSE SCORE", purpose_score, verbose)
    debug_print("PURPOSE REASON", purpose_reason, verbose)

    debug_print("6. GET SUBTITLES", "get_subtitles(txt_for_llm)", verbose)
    subtitles = get_subtitles(txt_for_llm)
    debug_print("SUBTITLES", subtitles, verbose)

    debug_print("7. GET SUMMARIES", "get_summaries(subtitles, language)", verbose)
    summaries = get_summaries(subtitles, language)
    debug_print("SUMMARIES", summaries, verbose)

    debug_print("8. CONTENT GRADE", "get_content_grade(purpose, summaries)", verbose)
    content_res = get_content_grade(purpose, summaries)
    debug_print("CONTENT RESULT RAW", content_res, verbose)

    if isinstance(content_res, tuple) and len(content_res) == 2:
        content_grade_val, off_topic_headings = content_res
    else:
        content_grade_val = content_res if isinstance(content_res, (int, float)) else 0.0
        off_topic_headings = []

    debug_print("CONTENT GRADE VALUE", content_grade_val, verbose)
    debug_print("OFF TOPIC HEADINGS", off_topic_headings, verbose)

    debug_print("9. RASTER FIGURES", "get_raster_figure_numbers(doc_obj)", verbose)
    raster_figure_numbers = get_raster_figure_numbers(doc_obj)
    debug_print("RASTER FIGURE NUMBERS", raster_figure_numbers, verbose)

    debug_print("10. IMAGE ANALYSIS", "analyze_images(doc_obj, mapped_doc)", verbose)
    raw_image_report = analyze_images(doc_obj, mapped_doc)
    debug_print("RAW IMAGE REPORT", raw_image_report, verbose)

    total_images = len(raw_image_report)
    bad_images_count = 0
    image_details_lines = []

    for item in raw_image_report:
        img_id = item.get("obrazek", item.get("id", "Nieznany"))
        is_correct = item.get("poprawnosc_danych", "True")
        errors = item.get("bledy", "None")

        if isinstance(errors, list):
            errors = " ".join(errors)

        if is_correct == "False" or is_correct is False:
            bad_images_count += 1
            status_text = "Wykryto rozbieznosci"
        else:
            status_text = "Poprawny"

        image_details_lines.append(
            f"Rysunek {img_id}: {status_text} - Szczegoly: {errors}"
        )

    image_summary_data = {
        "total": total_images,
        "bad_count": bad_images_count,
        "good_count": total_images - bad_images_count,
        "details": image_details_lines,
    }

    debug_print("IMAGE SUMMARY DATA", image_summary_data, verbose)

    debug_print("11. IMAGE QUALITY", "get_full_image_quality_json(...)", verbose)
    quality_errors = get_full_image_quality_json(
        doc_obj,
        mapped_doc,
        pdf_path,
        verbose=False,
    )

    debug_print("IMAGE QUALITY ERRORS", quality_errors, verbose)

    debug_print("12. FONT CONSISTENCY", "get_font_consistency_report(...)", verbose)
    font_errors = get_font_consistency_report(
        doc_obj,
        mapped_doc,
        verbose=False,
    )

    debug_print("FONT ERRORS", font_errors, verbose)

    cleanup_text_llm_instances(verbose=verbose)

    debug_print("13. SOTA", "get_final_sota_report(mapped_doc, language)", verbose)

    try:
        res_id, res_title, res_score, res_method, res_cites, r1, r2, r3 = get_final_sota_report(
            mapped_doc,
            language,
        )
        sota_error = None

    except Exception as sota_err:
        sota_error = str(sota_err)

        res_id, res_title, res_score, res_method, res_cites, r1, r2, r3 = (
            None,
            None,
            0,
            "Błąd SOTA",
            0,
            False,
            False,
            False,
        )

    debug_print("SOTA RESULT", {
        "id": res_id,
        "title": res_title,
        "score": res_score,
        "method": res_method,
        "citations": res_cites,
        "r1": r1,
        "r2": r2,
        "r3": r3,
        "sota_error": sota_error,
    }, verbose)

    debug_print("14. OVERALL GRADE", "get_overall_grade(...)", verbose)

    score = get_overall_grade(
        purpose_score,
        content_grade_val,
        res_score,
    )

    debug_print("OVERALL SCORE", {
        "purpose_score": purpose_score,
        "content_grade_val": content_grade_val,
        "sota_score": res_score,
        "overall_score": score,
    }, verbose)

    total_sections = len(summaries) if summaries else 1
    bad_sections = len(off_topic_headings)
    p_off_val = (bad_sections / total_sections) * 100.0 if total_sections > 0 else 0.0

    content_grade_dict = {
        "grade": round(score, 2),
        "max_grade": 100.0,
        "off_topic_sections": bad_sections,
        "p_off": round(p_off_val, 2),
        "off_topic_headings": off_topic_headings,
    }

    result = {
        "id": res_id,
        "tytul": res_title,
        "ocena": res_score,
        "podstawa": res_method,
        "cytowania": res_cites,
        "r1": r1,
        "r2": r2,
        "r3": r3,

        "purpose": purpose,
        "goal_result": goal_result,
        "purpose_score": purpose_score,
        "purpose_reason": purpose_reason,

        "content_grade": content_grade_dict,
        "image_analysis": image_summary_data,
        "jakosc_obrazkow": quality_errors,
        "czcionki_obrazkow": font_errors,
    }

    elapsed = time.perf_counter() - started

    debug_print("FINAL RESULT", result, verbose)
    debug_print("FINISHED", f"Execution time: {elapsed:.2f} s", verbose)

    return result, score, "Analiza LLM zakończona pomyślnie."


def main():
    print()
    print("=== TEST.PY LLM MODULE MAIN ===", flush=True)
    print(f"THESIS_PATH: {THESIS_PATH}", flush=True)
    print(f"LANGUAGE: {LANGUAGE}", flush=True)
    print("===============================", flush=True)
    print()

    if not THESIS_PATH.exists():
        print(f"ERROR: thesis file does not exist: {THESIS_PATH}", flush=True)
        return 1

    from analysis.extraction.extraction_json import extractPDF

    print("Extracting PDF with extractPDF...", flush=True)
    doc_obj = extractPDF(str(THESIS_PATH))
    print("extractPDF done.", flush=True)

    result, score, summary_text = run_llm_module(
        doc_obj=doc_obj,
        pdf_path=THESIS_PATH,
        language=LANGUAGE,
        verbose=True,
    )

    print()
    print("=== RETURN VALUES ===", flush=True)
    print(f"score: {score}", flush=True)
    print(f"summary_text: {summary_text}", flush=True)
    print("result:", flush=True)
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    print("=====================", flush=True)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print()
        print("=== TRACEBACK ===", flush=True)
        traceback.print_exc()
        raise