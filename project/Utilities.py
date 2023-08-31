import re
from typing import Optional

from spacy.matcher.matcher import Matcher
from spacy.tokens import Span, Token

from Constant import SUBJECT_PRONOUNS, OBJECT_PRONOUNS, STRING_EXCLUSION_LIST


def find_dependency(dependencies: [str], sentence: Span = None, token: Token = None, deep=False) -> [Token]:
    """
    find tokens that has the corresponding dependency in the specified dependencies list

    Args:
        dependencies: list of dependencies that we want to find
        sentence: do we want to find dependency in a sentence?
        token: or do we just to find dependency in the children of a token?
        deep: if true, the function will search the children's children for dependency, useful for compound dependency

    Returns:
        list of tokens

    """
    result = []

    if token is not None:
        if not deep:
            for child in token.children:
                if child.dep_ in dependencies:
                    result.append(child)
        else:
            for child in token.children:
                if child.dep_ in dependencies:
                    result.append(child)
                result.extend(find_dependency(dependencies, token=child, deep=True))

    elif sentence is not None:
        for token in sentence:
            for child in token.children:
                if child.dep_ in dependencies:
                    result.append(child)

    else:
        return []

    return result


def find_action(verb: Token, container):
    """
    given a verb in form of Token, find the corresponding action in the container

    Args:
        verb: the verb used to find the action
        container: the container that contains the action

    Returns:
        the action that corresponds to the verb

    """
    for process in container.processes:
        if process.action is not None and verb == process.action.token:
            return process.action
    return None


def find_actor(noun: Token, container):
    """
    given a noun in form of Token, find the corresponding actor in the container

    Args:
        noun: the noun used to find the actor
        container: the container that contains the actor

    Returns:
        the actor that corresponds to the noun

    """
    for process in container.processes:
        if process.actor is not None and noun == process.actor.token:
            return process.actor
    return None


def find_process(container, action=None, actor=None, sub_sent=None):
    """
    find the process that has the given action, actor, or sub_sentence

    Args:
        container: the container that contains the process
        action: action in the process
        actor: actor in the process
        sub_sent: sub_sentence in the process

    Returns:
        the founded process

    """
    if action is not None:
        for process in container.processes:
            if process.action is not None and process.action == action:
                return process

    if actor is not None:
        for process in container.processes:
            if process.actor is not None and process.actor == actor:
                return process

    if sub_sent is not None:
        for process in container.processes:
            if process.sub_sentence is not None and process.sub_sentence == sub_sent:
                return process

    return None


def contains_indicator(rules, sentence: Span, nlp) -> bool:
    """
    check if the sentence contains indicator specified in the given rules (spacy matchers)

    Args:
        rules: spacy matcher rules used to find the indicator
        sentence: the sentence to be checked
        nlp: spacy nlp language model

    Returns:
        True if the sentence contains the indicator, False otherwise

    """
    matcher = Matcher(nlp.vocab)
    for rule in rules:
        for k, v in rule.items():
            matcher.add(k, [v])

    matches = matcher(sentence)
    if len(matches) > 0:
        return True

    return False


def anaphora_resolver(obj):
    """
    resolve the anaphora in the given object

    Args:
        obj: the actor or resource to be resolved

    """
    if not needs_resolve_reference(obj.token):
        return
    resolved_words = resolve_reference(obj.token)
    obj.resolved_token.extend(resolved_words)



def needs_resolve_reference(word: Token) -> bool:
    """
    check if the given word needs to be resolved

    Args:
        word: the word to be checked

    Returns:
        True if the word needs to be resolved, False otherwise

    """
    if word.text.lower() in SUBJECT_PRONOUNS or word.text in OBJECT_PRONOUNS:
        return True
    return False


def resolve_reference(to_be_resolved_word: Token) -> [Token]:
    """
    resolve the given word

    Args:
        to_be_resolved_word: the word to be resolved

    Returns:
        the resolved word in form of list
    """
    if to_be_resolved_word is None:
        return []
    if to_be_resolved_word.doc._.coref_chains is None:
        return []

    resolved_word = to_be_resolved_word.doc._.coref_chains.resolve(to_be_resolved_word)
    if resolved_word is not None:
        return resolved_word
    else:
        return []


def belongs_to_other_process(root: Token, container):
    """
    check if the given root token belongs to other action

    Args:
        root: the root token to be checked
        container: the container that contains the whole processes

    Returns:
        the process contains the given root token, None otherwise

    """
    if len(list(root.ancestors)) > 0:
        ancestor = next(root.ancestors)
    else:
        ancestor = None
    if ancestor is not None:
        if ancestor.pos_ == "AUX" or ancestor.pos_ == "VERB":
            action = find_action(ancestor, container)
            if action is not None:
                process = find_process(container, action=action)
                return container.processes.index(process)
    return None


def get_complete_actor_name(main_actor):
    """
    get the complete actor name
    Args:
        main_actor: the main actor

    Returns:

    """
    result = []
    str_utility(main_actor, result)
    help_get_complete_actor_name(main_actor, result)
    if result[0].dep_ == "det" and result[0].text.lower() in ["the", "a", "an"]:
        result.remove(result[0])
    return string_list_to_string(result)


def help_get_complete_actor_name(main_actor, result):
    """
    help function for get_complete_actor_name
    Args:
        main_actor: the main actor
        result: the result list

    Returns:

    """
    for child in main_actor.children:
        if child.dep_ in ["compound", "det", "prep", "pobj", "appos", "amod", "nmod"] \
                and child.text.lower().strip() not in ["as", "within", "at", "of"]:
            help_get_complete_actor_name(child, result)
            str_utility(child, result)
    return result


def str_utility(string, string_list: [], i=None) -> []:
    """
    add the given token or string to the given string list in the correct order
    Args:
        string: the token or string that needs to be added
        string_list: the result list
        i: the index that the string needs to be inserted to, default is None

    Returns:

    """
    if isinstance(string, Token):
        s = string.text.lower()
    else:
        s = string.lower()

    if s in STRING_EXCLUSION_LIST:
        return

    if i is not None:
        insertion(string, string_list, i)
    elif len(string_list) == 0:
        string_list.append(string)
    else:
        insertion(string, string_list)


def insertion(string, string_list: [], i=None):
    """
    insert the given string to the given string list

    Args:
        string: the string that needs to be inserted
        string_list: the string list that the string needs to be inserted to
        i: the index that the string needs to be inserted to, default is None

    Returns:

    """
    for s in range(len(string_list)):
        if isinstance(string_list[s], str):
            continue
        if i is not None:
            index = i
        else:
            index = string.i

        if index < string_list[s].i:
            string_list.insert(s, string)
            return string_list
    string_list.append(string)


def string_list_to_string(string_list: []) -> str:
    """
    convert the given string list to string
    Args:
        string_list: the given string list

    Returns:
        the string converted from the given string list
    """
    result = ""

    for i in range(len(string_list)):
        if isinstance(string_list[i], str):
            result += string_list[i]
        else:
            result += string_list[i].text.lower()

        if i != len(string_list) - 1:
            result += " "

    return result


def index_of(item: Token, l: []) -> int:
    """
    get the index of the given item in the given list
    Args:
        item: the given item
        l: the given list

    Returns:
        the index of the given item in the list
    """
    for i in range(len(l)):
        if isinstance(l[i], str):
            if item.lemma_ == l[i]:
                return i
        elif isinstance(l[i], Token):
            if item == l[i]:
                return i
        else:
            continue


def text_pre_processing(text: str) -> str:
    """
    preprocess the given text, remove the text between brackets and replace two or more spaces with one
    Args:
        text: the given text in form of string

    Returns:
        the preprocessed text

    """
    # remove the text between brackets
    text = re.sub("[\(\[].*?[\)\]]", "", text)
    # replace two or more spaces with one
    text = re.sub(r"\s{2,}", " ", text)
    return text
