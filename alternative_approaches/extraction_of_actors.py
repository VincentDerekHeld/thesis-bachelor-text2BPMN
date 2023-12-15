"""
This file contains an alternative approach to extract the elements.
It is based on the description of the approach in the following paper.
Unfortunately, the paper does not contain any information about the code. Therefore, the code is based on the description in the paper. It is not the original code.

@article{sunDesigntimeBusinessProcess2023,
	title = {Design-{Time} {Business} {Process} {Compliance} {Assessment} {Based} on {Multi}-{Granularity} {Semantic} {Information}},
	issn = {0920-8542, 1573-0484},
	url = {https://link.springer.com/10.1007/s11227-023-05626-0},
	doi = {10.1007/s11227-023-05626-0},
	abstract = {Business process compliance is an essential part of business process management, which saves organizations from penalties caused by non-compliant processes. However, current researches on business process compliance mainly focus on checking using general constraint rules that have been formalized without in-depth analysis of related regulatory documents and mostly involve extensive human efforts. In this paper, we aim to propose an automatic and interpretable compliance checking approach for design-time business processes. By combining deep learning and a natural language processing approach based on rule templates, we extract semantic information from regulatory documents at different granularities for subsequent compliance checking. In addition, we match appropriate rules to the process model and detect the degree of violation of the business process from three controlflow perspectives. The effectiveness of this method is validated on two real-world datasets.},
	language = {en},
	urldate = {2023-10-06},
	journal = {The Journal of Supercomputing},
	author = {Sun, Xiaoxiao and Yang, Siqing and Zhao, Chenying and Yu, Dongjin},
	month = sep,
	year = {2023},
	file = {Sun et al. - 2023 - Design-time business process compliance assessment.pdf:/Users/vincentderekheld/Zotero/storage/NESYRM42/Sun et al. - 2023 - Design-time business process compliance assessment.pdf:application/pdf},
}
"""
from typing import Optional
from spacy.tokens import Span, Token
from project.ModelBuilder import create_actor, create_action

subject_dependencies = ["nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"]
object_dependencies = ["dobj", "dative", "attr", "oprd", "pobj", "iobj", "obj"]
check_for_actor_marker: bool = False

labels = ["MD", "NP", "VP", "IN", "PP", "SBAR", "SINV"]  # labels are in detail described in the paper

ACTOR_MARKERS = (
    "organization", "Organization", "the organization", "The organization", "sales", "department", "sales department",
    "the sales", "the sales department")


def immediately_dominates(A: Span, B: Span):
    # Check if the parent of B is A
    return B._.parent == A


def dominates(A: Span, B: Span) -> bool:
    """Checks if a span A dominates a span B in a syntactic dependency tree using spaCy. Notation: A << B
        Args:   A: Span of Spacy tokens in a syntactic dependency tree
                B: Span of Spacy tokens in a syntactic dependency tree
        Result: True if A dominates B, False otherwise
    """
    current = B
    while current._.parent is not None:
        if current._.parent == A:
            return True
        current = current._.parent
    return False


def are_sisters(span_A: Span, span_B: Span) -> bool:
    """Checks if two spans are sisters in a syntactic dependency tree using spaCy. Notation A $ B
        Args:   A: Span of Spacy tokens in a syntactic dependency tree
                B: Span of Spacy tokens in a syntactic dependency tree
        Results: True if A and B are sisters, False otherwise
    """
    return span_A.root.head == span_B.root.head


def check_labels(sent: Span, labels):
    """
    Checks if the given labels exist in the constituency parse of the doc.
    Returns a dictionary with the labels and their occurrence status.
    """
    results = {}
    for label in labels:
        results[label] = any(subtree._.labels == label for subtree in sent._.constituents)
    return results


def determine_NP(sent: Span) -> Span:
    """checking for a specific type of constituent: Noun Phrase ('NP')
        Args:  sent: Span of Spacy tokens in a syntactic dependency tree
        Result: The first noun phrase in the sentence
    """
    for const in sent._.constituents:
        if len(const._.labels) > 0 and const._.labels[0] == 'NP':
            return const


def check_for_label_dominating_actor_marker(sent: Span, label: str):  # subject dependency and NP < (actormarker)
    """
    Check if there's a noun phrase (NP) that immediately dominates any of the specified actor markers.
    Notation: subject dependency and NP < (actormarker)
    """
    results = []
    for subtree in sent._.constituents:
        if len(subtree._.labels) > 0 and subtree._.labels[0] == label:
            if check_for_actor_marker and any(token.text in ACTOR_MARKERS for token in subtree):
                results.append(subtree)
            elif not check_for_actor_marker:
                results.append(subtree)
    return results


def check_conditions1(sent: Span):
    """
    Check if there's a noun phrase (NP) that immediately dominates any of the specified actor markers. Notation: subject dependency and NP < (actormarker)
    """
    print("sent._.constituents", list(sent._.constituents))
    for subtree in sent._.constituents:
        if len(subtree._.labels) > 0 and subtree._.labels[0] == "NP" and any(
                token.text in ACTOR_MARKERS for token in subtree):
            for token in subtree:
                if token.dep_ in subject_dependencies:
                    print("Sentence: ", subtree.text)
                    return True
    return False


def check_conditions2(sent: Span):
    is_object_dependency = any(token.dep_ in ["dobj", "iobj", "obj"] for token in sent)
    is_passive_voice = any(token.dep_ == "auxpass" for token in sent)
    if not (is_object_dependency and is_passive_voice):
        return False
    for constituent in sent._.constituents:
        if constituent.label_ == "PP":
            for child in constituent._.children:
                if child.label_ == "IN":
                    for sibling in child._.siblings:
                        if sibling.label_ == "NP" and any(token.text in ACTOR_MARKERS for token in sibling):
                            return True
    return False


def check_conditions3(doc):
    # Check for object dependency
    is_object_dependency = any(token.dep_ in ["dobj", "iobj", "obj"] for token in doc)
    # Check for active voice (ensure no passive auxiliaries are present)
    is_active_voice = not any(token.dep_ == "auxpass" for token in doc)
    if not (is_object_dependency and is_active_voice):
        return False
    for constituent in doc._.constituents:
        if constituent.label_ == "NP" and any(token.text in ACTOR_MARKERS for token in constituent):
            return True
    return False


def find_constituents_by_label(sent: Span, label: str) -> list[Span]:
    results = []
    for constituents in sent._.constituents:
        if label in constituents._.labels:
            results.append(constituents)
    return results


def determine_actor_sun(sentence: Span) -> Span | None:
    """This metod is used to eveluate the approach of Sun et. al to extract the actor of a sentence."""
    'Condition 1: subject dependency and NP < (actormarker)'
    for possible_actor in check_for_label_dominating_actor_marker(sentence, "NP"):
        if any(token.dep_ in subject_dependencies for token in possible_actor):
            return possible_actor

    'Condition 2: object dependency and passive voice and PP < IN$(NP < (actormarker))'
    for possible_actor in check_for_label_dominating_actor_marker(sentence, "NP"):
        is_object_dependency = any(token.dep_ in object_dependencies for token in possible_actor)
        is_passive_voice = any(token.dep_ == "auxpass" for token in sentence)
        if not (is_object_dependency and is_passive_voice):
            return None
        else:
            for possible_PP in find_constituents_by_label(sentence, "PP"):
                for token in possible_PP:
                    if token.text == 'by' and 'IN' == token.tag_:
                        span_by = sentence[token.i:token.i + 1]
    'Condition 3: object dependency and active voice and NP < (actormarker))'
    for possible_actor in check_for_label_dominating_actor_marker(sentence, "NP"):
        is_object_dependency = any(token.dep_ in object_dependencies for token in possible_actor)
        is_active_voice = not any(token.dep_ == "auxpass" for token in sentence)
        if not (is_object_dependency and is_active_voice):
            return None
        else:
            return possible_actor


def determine_predicate_vh(sentence: Span, active, actor):
    print("actor[0].ancestors:", actor[0].ancestors)
    if actor is not None and len(actor) > 0:
        verb = next(actor[0].ancestors)
        print("verb:", verb)
        return verb
    return None


def determine_object_vh(predicate: Token, active: bool) -> Optional[Token]:
    from project.Utilities import find_dependency
    if active:
        if predicate is None:
            return None
        obj = find_dependency(["dobj"], token=predicate)
        if len(obj) == 0:
            prep = find_dependency(["prep"], token=predicate)
            if len(prep) > 0:
                obj = find_dependency(["pobj"], token=prep[0])
    else:
        obj = find_dependency(["nsubjpass"], token=predicate)
    if len(obj) > 0:
        return obj[0]
    return None


def extract_elements_vh(sentence, process):
    from project.AnalyzeSentence import is_active
    sentence_is_active = is_active(sentence)
    actor = determine_actor_sun(sentence)
    if actor:
        actor = actor[actor.__len__() - 1]
    print("actor:", actor)
    # actor = determine_actor(actor, sentence_is_active)
    process.actor = create_actor(actor)
    from project.AnalyzeSentence import determine_predicate
    verb = determine_predicate(sentence, sentence_is_active)
    obj = determine_object_vh(verb, sentence_is_active)
    process.action = create_action(verb, obj)
    if verb:
        for child in verb.children:
            if child.dep_ == "aux": print(f"Extraction: modal verb:{child.text}")
    if process.action is not None:
        process.action.active = sentence_is_active
        for conjunct in process.action.token.conjuncts:
            if conjunct == process.action.token:
                continue
            if sentence.start < conjunct.i < sentence.end:
                conjunct_obj = determine_object_vh(conjunct, sentence_is_active)
                conjunct_action = create_action(conjunct, conjunct_obj)
                process.action.conjunction.append(conjunct_action)
