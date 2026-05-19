'''
Funkcja sprawdzająca czy błąd typograficzny po złączeniu z najbliższymi spanami dalej jest błędem typograficznym
'''
import json
import re
from .language_error_extractor import typo_check

def is_word_correct(word, language):
    if not word: return False
    return typo_check(word)

def refine_typos(errors, blocks, output_json="typos.json"):
    """
    Post-processing błędów. Przechodzi przez literówki i sprawdza, 
    czy po złączeniu ze słowami obok przestają być błędami.
    """
    block_info_map = {}
    for b in blocks:
        if b.block.type not in {"acronym", "keywords"}:
            block_info_map[b.block.block_id] = {
                "contents": b.contents,
                "language": b.language
            }

    final_errors = []
    typos_report = {"before_total": len(errors), "resolved_typos": [], "after_total": 0}

    for err in errors:
        if err.category != "TYPOS":
            final_errors.append(err)
            continue
            
        b_info = block_info_map.get(err.block_id)
        if not b_info:
            final_errors.append(err)
            continue
            
        contents = b_info["contents"]
        lang = b_info["language"]
        typo_text = err.content
        
        context_left = contents[max(0, err.offset - 30):err.offset]
        context_right = contents[err.offset + err.error_length:min(len(contents), err.offset + err.error_length + 30)]
        
        left_match = re.search(r'(\w+)[^\w]*$', contents[:err.offset])
        left_word = left_match.group(1) if left_match else ""
        
        right_match = re.search(r'^[^\w]*(\w+)', contents[err.offset + err.error_length:])
        right_word = right_match.group(1) if right_match else ""

        is_resolved = False
        resolved_word = ""
        
        if left_word and not is_resolved:
            merged_left = left_word + typo_text
            if is_word_correct(merged_left, lang):
                is_resolved = True
                resolved_word = merged_left

        if right_word and not is_resolved:
            merged_right = typo_text + right_word
            if is_word_correct(merged_right, lang):
                is_resolved = True
                resolved_word = merged_right

        if is_resolved:
            typos_report["resolved_typos"].append({
                "original_typo": typo_text,
                "resolved_as": resolved_word,
                "context": f"...{context_left}[{typo_text}]{context_right}...",
                "language": lang
            })
        else:
            final_errors.append(err)

    # typos_report["after_total"] = len(final_errors)
    # try:
    #     with open(output_json, "w", encoding="utf-8") as f:
    #         json.dump(typos_report, f, ensure_ascii=False, indent=4)
    # except Exception as e:
    #     print(f"Nie udało się zapisać {output_json}: {e}")

    return final_errors