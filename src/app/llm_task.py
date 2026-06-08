import gc
import traceback


def cleanup_text_llm_instances():
    """
    Release text LLM instances to reduce RAM/VRAM usage between LLM stages.
    """

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

    except Exception:
        pass

    gc.collect()

    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass


def build_image_summary(raw_image_report):
    """
    Build image_analysis dictionary in the same format as the old pipeline task_llm.
    """

    if raw_image_report is None:
        raw_image_report = []

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

    return {
        "total": total_images,
        "bad_count": bad_images_count,
        "good_count": total_images - bad_images_count,
        "details": image_details_lines,
    }


def run_task_llm(doc_obj, pdf_path, language="pl", use_llm=True):
    """
    Run the LLM part of the analysis pipeline.

    Return format is intentionally identical to the old nested task_llm():

        result, score, summary_text
    """

    if not use_llm:
        return None, None, "Tryb Szybki."

    try:
        from analysis.extraction.helper_llm.converter_linguistics_llm import get_plain_text
        from analysis.extraction.helper_llm.extraction_json_llm import extractPDF_llm

        from analysis.modules.llm.get_grade import get_overall_grade, get_content_grade
        from analysis.modules.llm.get_purpose import get_purpose
        from analysis.modules.llm.goal_realization import (
            check_goal_realization,
            get_score_from_goal_result,
        )
        from analysis.modules.llm.get_summary import get_summaries
        from analysis.modules.llm.get_subtitles import get_subtitles
        from analysis.modules.llm.run_sota import get_final_sota_report

        from analysis.modules.llm.image_analysis.run_image import analyze_images
        from analysis.modules.llm.image_analysis.image_quality_checker import (
            get_full_image_quality_json,
        )
        from analysis.modules.llm.image_analysis.font_checker import (
            get_font_consistency_report,
        )

        from analysis.extraction.converter_linguistics_clean import PDFMapper

        mapper = PDFMapper()
        mapped_doc = mapper.map_to_schema(doc_obj)

        plain_txt_purpose = get_plain_text(pdf_path)
        txt_for_llm = extractPDF_llm(pdf_path)

        if not plain_txt_purpose:
            raise ValueError("plain_txt_purpose is empty")

        if txt_for_llm is None:
            raise ValueError("extractPDF_llm returned None")

        purpose = get_purpose(plain_txt_purpose, language)

        goal_result = check_goal_realization(
            text=plain_txt_purpose,
            purpose=purpose,
            language=language,
        )

        purpose_score = get_score_from_goal_result(goal_result)
        purpose_reason = str(goal_result.get("reason", "") or "")

        cleanup_text_llm_instances()

        subtitles = get_subtitles(txt_for_llm)
        summaries = get_summaries(subtitles, language)

        content_res = get_content_grade(purpose, summaries)

        if isinstance(content_res, tuple) and len(content_res) == 2:
            content_grade_val, off_topic_headings = content_res
        else:
            content_grade_val = content_res if isinstance(content_res, (int, float)) else 0.0
            off_topic_headings = []

        cleanup_text_llm_instances()

        try:
            raw_image_report = analyze_images(doc_obj, mapped_doc)
        except Exception:
            raw_image_report = []

        image_summary_data = build_image_summary(raw_image_report)

        cleanup_text_llm_instances()

        try:
            quality_errors = get_full_image_quality_json(
                doc_obj,
                mapped_doc,
                pdf_path,
                verbose=False,
            )
            if quality_errors is None:
                quality_errors = []
        except Exception:
            quality_errors = []

        cleanup_text_llm_instances()

        try:
            font_errors = get_font_consistency_report(
                doc_obj,
                mapped_doc,
                verbose=False,
            )
            if font_errors is None:
                font_errors = []
        except Exception:
            font_errors = []

        cleanup_text_llm_instances()

        res_id, res_title, res_score, res_method, res_cites, r1, r2, r3 = (
            get_final_sota_report(mapped_doc, language)
        )

        score = get_overall_grade(
            purpose_score,
            content_grade_val,
            res_score,
        )

        total_sections = len(summaries) if summaries else 1
        bad_sections = len(off_topic_headings)
        p_off_val = (bad_sections / total_sections) * 100.0 if total_sections > 0 else 0.0

        content_grade_dict = {
            "grade": round(score, 2),
            "max_grade": 100.0,
            "off_topic_sections": bad_sections,
            "p_off": round(p_off_val, 2),
            "off_topic_headings": off_topic_headings,
            "purpose_reason": purpose_reason,
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
            "content_grade": content_grade_dict,
            "image_analysis": image_summary_data,
            "jakosc_obrazkow": quality_errors,
            "czcionki_obrazkow": font_errors,
        }

        return result, score, "Analiza LLM zakończona pomyślnie."

    except Exception:
        traceback.print_exc()
        return None, None, "Błąd analizy SOTA/LLM."