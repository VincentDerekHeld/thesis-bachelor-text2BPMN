"""
This file contains an alternative approach to extract the elements.
It is based on the description of the approach in the following paper.
Unfortunately, the paper does not contain any information about the code.
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

# from project.AnalyzeSentence import is_active, determine_actor, determine_predicate, determine_object, create_actor, create_action
from typing import Any, Optional

import benepar, spacy
from spacy import Language
from spacy.tokens import Span, Token
from project.ModelBuilder import create_actor, create_action

"""
def extract_elements(sentence, process):
    sentence_is_active = is_active(sentence)

    actor = determine_actor(sentence, sentence_is_active)
    process.actor = create_actor(actor)

    verb = determine_predicate(sentence, sentence_is_active)
    obj = determine_object(verb, sentence_is_active)
    process.action = create_action(verb, obj)
"""
subject_dependencies = ["nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"]
object_dependencies = ["dobj", "dative", "attr", "oprd", "pobj", "iobj", "obj"]
check_for_actor_marker: bool = False


def immediately_dominates(A: Span, B: Span):
    # Check if the parent of B is A
    return B._.parent == A


# Another function to check if A dominates B
def dominates(A: Span, B: Span):
    current = B
    while current._.parent is not None:
        if current._.parent == A:
            return True
        current = current._.parent
    return False


def are_sisters(span_A: Span, span_B: Span):
    # Assuming span_A and span_B are two spans you're comparing
    print("span_A.root.head:", span_A.root.head)
    print("span_B.root.head:", span_B.root.head)
    return span_A.root.head == span_B.root.head


def check_labels(sent, labels):
    """
    Checks if the given labels exist in the constituency parse of the doc.
    Returns a dictionary with the labels and their occurrence status.
    """
    results = {}
    for label in labels:
        results[label] = any(subtree._.labels == label for subtree in sent._.constituents)
    return results


def determine_NP(sent) -> Span:
    for const in sent._.constituents:
        if len(const._.labels) > 0 and const._.labels[0] == 'NP':
            return const


labels = ["MD", "NP", "VP", "IN", "PP", "SBAR", "SINV"]  # labels are in detail described in the paper

ACTOR_MARKERS = (
    "organization", "Organization", "the organization", "The organization", "sales", "department", "sales department",
    "the sales", "the sales department")


def check_for_label_dominating_actor_marker(sent: Span, label: str):  # subject dependency and NP < (actormarker)
    """
    Check if there's a noun phrase (NP) that immediately
    dominates any of the specified actor markers.
    """
    results = []
    for subtree in sent._.constituents:
        if len(subtree._.labels) > 0 and subtree._.labels[0] == label:
            if check_for_actor_marker and any(token.text in ACTOR_MARKERS for token in subtree):
                results.append(subtree)
            elif not check_for_actor_marker:
                results.append(subtree)
    return results


def check_conditions1(sent: Span):  # subject dependency and NP < (actormarker)
    """
    Check if there's a noun phrase (NP) that immediately
    dominates any of the specified actor markers.
    """
    print("sent._.constituents", list(sent._.constituents))
    for subtree in sent._.constituents:
        """if len(subtree._.labels) > 0:
            #print("subtree._.labels", subtree._.labels, "len(subtree._.labels) > 0", len(subtree._.labels) > 0, "subtree._.labels[0] == NP ", subtree._.labels[0], "Token:", any(
                token.text in ACTOR_MARKERS for token in subtree).__str__())
        for token in subtree:
            print("Token:", token.text)"""
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


def determine_actor_vh(sentence: Span) -> Span | None:
    'Condition 1: subject dependency and NP < (actormarker)'
    for possible_actor in check_for_label_dominating_actor_marker(sentence, "NP"):
        if any(token.dep_ in subject_dependencies for token in possible_actor):
            return possible_actor

    'Condition 2: object dependency and passive voice and PP < IN$(NP < (actormarker))'
    for possible_actor in check_for_label_dominating_actor_marker(sentence, "NP"):
        print("possible_actor:", possible_actor)
        is_object_dependency = any(token.dep_ in object_dependencies for token in possible_actor)
        print("is_object_dependency:", is_object_dependency)
        is_passive_voice = any(token.dep_ == "auxpass" for token in sentence)
        print("is_passive_voice:", is_passive_voice)
        if not (is_object_dependency and is_passive_voice):
            print("not (is_object_dependency and is_passive_voice)")
            return None
        else:
            print("(is_object_dependency and is_passive_voice)")
            print("find_constituents_by_label", find_constituents_by_label(sentence, "PP"))
            print("possible_actor:", possible_actor)
            for possible_PP in find_constituents_by_label(sentence, "PP"):
                print("possible_PP:", possible_PP)
                for token in possible_PP:
                    print("child.text:", token.text, token.dep_, token.pos_, token.tag_)
                    if token.text == 'by' and 'IN' == token.tag_:
                        span_by = sentence[token.i:token.i + 1]
                        print(span_by)
                        print(immediately_dominates(possible_PP, span_by))
                        print(are_sisters(span_by, possible_actor))
                        print("Success!")
                # if are_sisters(possible_PP, possible_actor):
                #   for child in possible_PP._.children:
                #      print("child.text:", child.text, "child.dep_:", child.dep_)
                #     if child.text == "by":
                #        return possible_actor

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
    actor = determine_actor_vh(sentence)
    from project.AnalyzeSentence import determine_actor
    print("determine_actor_vh: actor:", actor)
    # print(actor.__len__())
    if actor:
        actor = actor[actor.__len__() - 1]  # TODO:
    print("actor:", actor)
    # actor = determine_actor(actor, sentence_is_active)
    process.actor = create_actor(actor)

    from project.AnalyzeSentence import determine_predicate
    verb = determine_predicate(sentence, sentence_is_active)
    ##TODO: find modal verb as well

    obj = determine_object_vh(verb, sentence_is_active)
    process.action = create_action(verb, obj)
    if verb:
        for child in verb.children:
            if child.dep_ == "aux": print(f"Extraction: modal verb:{child.text}")
    # print(f"Extraction: verb: {verb}, verb.subtree: {' '.join(x.text for x in verb.children)}")

    if process.action is not None:
        process.action.active = sentence_is_active
        for conjunct in process.action.token.conjuncts:
            if conjunct == process.action.token:
                continue
            if sentence.start < conjunct.i < sentence.end:
                conjunct_obj = determine_object_vh(conjunct, sentence_is_active)
                conjunct_action = create_action(conjunct, conjunct_obj)
                ##TODO: find modal verb as well
                process.action.conjunction.append(conjunct_action)


"""
for const in sent._.constituents:
    if len(const._.labels) > 0 and const._.labels[0] == 'NP':
        print(const.text)"""

"""
 for token in sentence:
    print("token.sent._.labels:", token.sent._.labels)
    if token.dep_ in subject_dependencies and "NP" in token.sent._.labels:
        return token.text
    elif token.dep_ in object_dependencies and sentence_is_active == False and "PP" in token.sent._.labels:
        return token.text
    elif token.dep_ in object_dependencies and sentence_is_active == True and "NP" in token.sent._.labels:
        return token.text
"""

"""sent = list(doc.sents)[0]
constituents = list(sent._.constituents)
for const in constituents:
    # if len(const._.labels) > 0:
    print("const:", const, "*" * 20, "const._.labels", const._.labels)

A: Span = constituents[0]
print("A:", A.text)  # This is just an example, choose your own constituents.
B: Span = constituents[3]
print("B:", B.text)
print(dominates(A, B).__str__())"""
#

# determine_actor_vh(sent, True)
# print(are_sisters(sent._.constituents[0], sent._.constituents[1]).__str__())
# for const in sent._.constituents:
#   if len(const._.labels) > 0:
#      print("const:", const, "*" * 20, "const._.labels", const._.labels)


# if len(const._.labels)> 0 and const._.labels[0] == 'VP':
#   print(const.text)

# sent = list(doc.sents)[0]
# print(sent._.parse_string)
# (S (NP (NP (DT The) (NN time)) (PP (IN for) (NP (NN action)))) (VP (VBZ is) (ADVP (RB now))) (. .))
# print(sent._.labels)
# ('S',)
# print(list(sent._.children)[0])

# print(determine_actor_vh(sent, True))
