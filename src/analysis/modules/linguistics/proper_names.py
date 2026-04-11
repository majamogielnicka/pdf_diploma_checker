from .spacy_helpers import nlp_pl, nlp_en
from src.analysis.extraction.schema import ParagraphBlock, ListBlock
import re


def get_proper_names(document, text_language):
    """
    Extracts proper names and recognized entities from the document using spaCy.
    
    Args:
        document (FinalDocument): The document structure.
        text_language (str): The language code of the text.
        
    Returns:
        set: A set containing unique valid proper names extracted from the text.
    """

    proper_names = []
    
    if text_language == "pl":
        nlp = nlp_pl
    else:
        nlp = nlp_en

    for block in document.logical_blocks:

        if block.type == "paragraph":

            if text_language == "pl":
                text = nlp(block.content)
                for ent in text.ents:
                    if ent.label_:
                        if ent.label_ == "date" or ent.label_ == "time":
                            continue
                        proper_names.append(ent.text)

            elif text_language == "en":
                text = nlp(block.content)
                for ent in text.ents:   
                    if ent.label_:
                        if ent.label_ == "TIME" or ent.label_ == "DATE" or ent.label_ == "CARDINAL" or ent.label_ == "MONEY" or ent.label_ == "PERCENT" or ent.label_ == "QUANTITY" or ent.label_ == "ORDINAL":
                            continue
                        proper_names.append(ent.text) 

        if block.type == "keywords":
            if re.search("^Słowa kluczowe|^Keywords|^keywords|^słowa kluczowe", block.content):
                content = re.split(":", block.content)
                keywords = re.split(",|;", content[1])
                proper_names.extend(keywords)

        if isinstance(block, ListBlock):
            for item in block.items:
                if text_language == "pl":
                    text = nlp(item.text)
                    for ent in text.ents:
                        if ent.label_:
                            if ent.label_ == "date" or ent.label_ == "time":
                                continue
                            proper_names.append(ent.text) 

                elif text_language == "en":
                    text = nlp(item.text)
                    for ent in text.ents:
                        if ent.label_:
                            if ent.label_ == "TIME" or ent.label_ == "DATE" or ent.label_ == "CARDINAL" or ent.label_ == "MONEY" or ent.label_ == "PERCENT" or ent.label_ == "QUANTITY" or ent.label_ == "ORDINAL":
                                continue
                            proper_names.append(ent.text)  

    proper_names = set(proper_names)
    #print(proper_names)
    return proper_names