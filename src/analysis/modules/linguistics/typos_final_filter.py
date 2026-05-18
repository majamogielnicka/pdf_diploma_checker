'''
Funkcja sprawdzająca czy błąd typograficzny po złączeniu z najbliższymi spanami dalej jest błędem typograficznym
'''
import json
import re
import language_tool_python
from .helpers import morf

_tool_en = None

def get_tool_en():
    global _tool_en
    if _tool_en is None:
        _tool_en = language_tool_python.LanguageTool('en-GB')
    return _tool_en

def pl_typo_check(typo_text):
    analysis = morf.analyse(typo_text)
    for interpretation in analysis:
        tag = interpretation[2][2]
        if tag == "ign":
            return False
    return True

def is_word_correct(word, language):
    if not word: return False
    if language == 'pl':
        return pl_typo_check(word)
    else:
        tool = get_tool_en()
        # Zwraca True, jeśli po złączeniu LanguageTool nie zwraca TYPOS
        return len([m for m in tool.check(word) if m.category == 'TYPOS']) == 0

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

    typos_report["after_total"] = len(final_errors)
    try:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(typos_report, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Nie udało się zapisać {output_json}: {e}")

    return final_errors