import spacy
import functools

nlp_en = spacy.load('en_core_web_sm')
nlp_pl = spacy.load('pl_core_news_md')

@functools.cache
def lemmatization(word_base, text_language):
    '''
    Extracts the lemma of a word
    
    Args:
        word (str): Word to be checked
        text_language (str): pl for Polish or en for English.
    
    Returns:
        tuple(lemma(str), is_found(bool)): A tuple of extracted word and bolean value True if lemma has been found. 
    '''
    word = word_base.lower()
    if text_language == "pl":
        nlp = nlp_pl
    else:
        nlp = nlp_en
    nlp_word = nlp(word)
    lemma = word
    for token in nlp_word:
        lemma = token.lemma_
    is_found = True
    if lemma == word:
        is_found = False
    return lemma, is_found