import spacy

from Constant import PERSON_CORRECTOR_LIST, REAL_ACTOR_DETERMINERS, SUBJECT_PRONOUNS, LLM_real_actor
from spacy_wordnet.wordnet_annotator import WordnetAnnotator

from project.LLM_API import generate_response_GPT4_model, normalize_boolean_result


def can_be_person_or_system(full_noun: str, main_noun) -> bool:
    full_noun = full_noun.strip()
    # print(f"full noun: {full_noun.lower()}, if full_noun.lower() in PERSON_CORRECTOR_LIST {full_noun.lower() in PERSON_CORRECTOR_LIST}")
    if full_noun.lower() in PERSON_CORRECTOR_LIST:
        return True
    elif main_noun.text.lower() in SUBJECT_PRONOUNS:
        return False
    elif main_noun.pos_ == "PRON":
        return False

    synsets = main_noun._.wordnet.synsets()
    if len(synsets) == 0:
        return False
    elif can_be(synsets[0], []):
        return True
    elif LLM_real_actor:
        if decide_if_real_actor(full_noun.lower()):
            return True
    else:
        return False


def can_be(synset, checked_words: list):
    """
    Args:
        synset: wordnet synset (set of synonyms)
        checked_words:
    Returns:
        bool: True if the hypernym of the synset is a part of the REAL_ACTOR_DETERMINERS list or checked_words list
    """
    if not synset.name() in checked_words:
        checked_words.append(synset.name())
        hypernyms = synset.hypernyms()
        if len(hypernyms) == 0:
            return False
        hypernym_name = hypernyms[0].lemma_names()[0]
        if hypernym_name in REAL_ACTOR_DETERMINERS:
            return True
        else:
            hypernyms = synset.hypernyms()
            if can_be(hypernyms[0], checked_words):
                return True
    else:
        return False


def hypernyms_checker(token, stop_list: list) -> bool:
    if token.text.lower() in stop_list:
        return True

    synsets = token._.wordnet.synsets()
    if len(synsets) == 0:
        return False
    elif can_be_checked_token(synsets[0], [], stop_list):
        return True
    else:
        return False


def verb_hypernyms_checker(token, stop_list: list) -> bool:
    if token.text.lower() in stop_list:
        return True

    synsets = token._.wordnet.synsets()
    if len(synsets) == 0:
        return False
    for synset in synsets:
        if can_be_checked_token(synset, [], stop_list):
            return True
    else:
        return False


def can_be_checked_token(synset, checked_words: list, stop_list: list):
    if not synset.name() in checked_words:
        checked_words.append(synset.name())
        hypernyms = synset.hypernyms()
        if len(hypernyms) == 0:
            return False
        hypernym_name = hypernyms[0].lemma_names()[0]

        # print(hypernym_name)

        if hypernym_name in stop_list:
            return True
        else:
            hypernyms = synset.hypernyms()
            if can_be_checked_token(hypernyms[0], checked_words, stop_list):
                return True
    else:
        return False


def decide_if_real_actor(text_input: str) -> bool:
    debug_mode = True
    prompt = (f"""
        Defintion of a real actor: A real actor is a person, a group, a department, a system, a place location, a profession or a occupation that is involved in the process.
        If yes, return only "True", otherwise return only "False".
        Carefully determine if the following text describes a real actor (based on the definition of a real actor):
        ### Text: ###
        {text_input}
        """)
    result = ""
    result = generate_response_GPT4_model(prompt).strip()
    result = normalize_boolean_result(result)
    if debug_mode: print(f"decide_if_real_actor: {result}: {text_input}")
    return result


if __name__ == '__main__':
    nlp = spacy.load('en_core_web_sm')
    nlp.add_pipe("spacy_wordnet", after='tagger')
    text_input = "the claim is rejected"
    document = nlp(text_input)
    hypernyms_checker(document[1], [])
    print("-" * 20)
    verb_hypernyms_checker(document[3], [])
