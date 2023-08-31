from typing import Optional
from spacy.tokens import Doc, Span, Token
from Model.Process import Process
from Model.Resource import Resource
from Model.SentenceContainer import SentenceContainer
from Utilities import find_dependency
from ModelBuilder import create_actor, create_action, correct_model


def sub_sentence_finder(sentence: Span) -> [Span]:
    """find the potential sub-sentences of a sentence, when the sentence has no sub-sentence, return the sentence itself
       in a List.

       Args:
           sentence: The sentence whose sub-sentence must be found
           doc: The document that contains the sentence

       Returns:
           A list of sub-sentences
    """
    sentence_list = find_sub_sentence_start_end_index(sentence, [])
    sentence_list.sort()
    result = []
    symbols = ['.', ',', ';', ':', '!', '?', '(', ')', '[', ']', '{', '}', '"', "'", '``', "''", '“', '”', '‘', '’',
               '—']

    for i in range(len(sentence_list) - 1):
        left = sentence_list[i]
        right = sentence_list[i + 1]
        sentence = sentence.doc[left:right]
        if sentence.text in symbols:
            continue
        result.append(sentence)

    return result


def find_sub_sentence_start_end_index(sentence: Span, index_list: [int]):
    """find the start and end index of the sub-sentences

       Args:
           sentence: The sentence whose sub-sentence must be found
           index_list: The list of start and end index of sub-sentences

       Returns:
           A list int number, representing the start and end index of sub-sentences
    """
    labels = sentence._.labels

    if len(labels) == 0:
        return index_list
    elif "SBAR" in labels:
        index_list = add_index(index_list, sentence.start)
        index_list = add_index(index_list, sentence.end)
    elif "S" in labels:
        if sentence._.parent is None:
            index_list = add_index(index_list, sentence.start)
            index_list = add_index(index_list, sentence.end)
        elif not "SBAR" in sentence._.parent._.labels:
            index_list = add_index(index_list, sentence.start)
            index_list = add_index(index_list, sentence.end)

    children = list(sentence._.children)

    for sub_sentence in children:
        find_sub_sentence_start_end_index(sub_sentence, index_list)

    return index_list


def add_index(index_list, index):
    if index in index_list:
        return index_list
    else:
        index_list.append(index)
        return index_list


def analyze_document(doc: Doc) -> [SentenceContainer]:
    """Analyze the document and return a list of SentenceContainer which contains the extracted information stored in
        the models.

       Args:
           nlp: The spacy language model
           doc: The document that contains the sentence

       Returns:
           A list SentenceContainer
    """
    container_list = []
    for sentence in doc.sents:
        container = SentenceContainer(sentence)
        container_list.append(container)

        sub_sentence_list = sub_sentence_finder(sentence)
        for sub_sentence in sub_sentence_list:
            process = Process(sub_sentence)
            extract_elements(sub_sentence, process)
            container.add_process(process)

    for sentence in container_list:
        complement_actor(sentence)
        complement_object(sentence)
        correct_model(sentence)
        complement_model(sentence)

    return container_list


def extract_elements(sentence, process):
    """
    extract the elements from the sentence, creating the corresponding models, and adding them to the processes

    Args:
        sentence: the complete sentence
        process: the process where the elements should be determined and then be added to
        nlp: the spacy language model
    """
    sentence_is_active = is_active(sentence)

    actor = determine_actor(sentence, sentence_is_active)
    process.actor = create_actor(actor)

    verb = determine_predicate(sentence, sentence_is_active)
    obj = determine_object(verb, sentence_is_active)
    process.action = create_action(verb, obj)

    if process.action is not None:
        process.action.active = sentence_is_active

        for conjunct in process.action.token.conjuncts:
            if conjunct == process.action.token:
                continue
            if sentence.start < conjunct.i < sentence.end:
                conjunct_obj = determine_object(conjunct, sentence_is_active)
                conjunct_action = create_action(conjunct, conjunct_obj)
                process.action.conjunction.append(conjunct_action)


def is_active(sentence: Span) -> bool:
    """ determine whether the sentence is in active or in passive voice

        Args:
            sentence: A sentence whose voice should be determined.

        Returns:
            return True if the sentence is in active voice, False otherwise
    """
    passive_tense = [tok for tok in sentence if (tok.dep_ == 'auxpass')]
    return not len(passive_tense) > 0


def determine_actor(sentence: Span, active: bool) -> Optional[Token]:
    """ extract the actor(subject) of the sentence

        Args:
            sentence: A sentence whose actor should be determined.
            active: A boolean value indicating whether the sentence is in active voice or not

        Returns:
            if the actor is identified, return it as a token, otherwise return None
    """

    if active:
        # find whether the sentence has "nsubj" dependency -> the subject of the sentence
        search = find_dependency(["nsubj"], sentence=sentence)
        main_actor = search[0] if len(search) > 0 else None
    else:
        # find whether the sentence has "agent" dependency -> the "by" in the sentence
        agent = find_dependency(["agent"], sentence=sentence)
        main_actor = next(agent[0].children) if len(agent) > 0 else None

    return main_actor


def determine_predicate(sentence: Span, active: bool) -> Optional[Token]:
    """extract the verb of the sentence

       Args:
           sentence: sentence: A sentence whose action(s) should be determined.
           active: A boolean value indicating whether the sentence is in active voice or not

       Returns:
           if the verb is identified, return it as a token, otherwise return None
    """

    if active:
        actor = find_dependency(["nsubj"], sentence=sentence)
        if len(actor) == 0:
            actor = find_dependency(["dobj"], sentence=sentence)

    else:
        actor = find_dependency(["nsubjpass"], sentence=sentence)

    if len(actor) > 0:
        verb = next(actor[0].ancestors)
        return verb

    return None


def determine_object(predicate: Token, active: bool) -> Optional[Token]:
    """extract the object of the sentence

       Args:
           predicate: The verb in the sentence.
           active: A boolean value indicating whether the sentence is in active voice or not

       Returns:
           if there is a direct object, return it as a token, otherwise return None
    """

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


def complement_model(container: SentenceContainer):
    """
    add the conjunctions of the actions to the list of processes, conjunctions are originally detected but only store as
    an attribute in the action, this function extract the conjunctions and tried to find the proper place to add them

    Args:
        container: The container that contains the action.

    """
    new_processes = container.processes.copy()
    for process in container.processes:
        if process.action is None:
            continue

        # add the conjunctions to the list
        if len(process.action.conjunction) > 0:
            index_in_list = new_processes.index(process)
            for conjunction in process.action.conjunction:
                # if the process doesn't have an object, the real object might belong to the conjunction
                if process.action.object is None and conjunction.object is not None:
                    process.action.object = conjunction.object

                # to determine whether to add the conjunctions before or after this process
                if conjunction.token.i < process.action.token.i:
                    index_in_list -= 1
                # create a new process for the conjunction
                conjunction_process = Process(process.sub_sentence)
                conjunction_process.action = conjunction
                if conjunction.object is None:
                    conjunction_process.action.object = process.action.object
                conjunction_process.actor = process.actor

                new_processes.insert(index_in_list + 1, conjunction_process)
                index_in_list += 1

    # substitute the old processes with the new ones (because we performed the adding element in the loop)
    container.processes = new_processes


def complement_actor(container: SentenceContainer):
    """
    some process only has an action but no actor, this is caused because the actor is in the main clause or the actor belongs
    to the conjunction, this function tries to find the actor of the process and add it to the process

    Args:
        container: The container that contains the action.
    """
    for process in container.processes:
        if process.action is not None:
            if process.actor is None:
                token = process.action.token
                xcomp_token = find_xcomp_ancestor(token)
                if xcomp_token is not None:
                    father = belongs_to_action(container, xcomp_token)
                    if father is not None:
                        if father.actor is not None:
                            process.actor = father.actor
                            return
                elif process.action.token.dep_ in ["ccomp", "acl"]:
                    verb = next(process.action.token.ancestors)
                    if verb.pos_ == "NOUN":
                        verb = next(verb.ancestors)
                    dative = find_dependency(["dative", "prep"], token=verb)
                    if len(dative) > 0:
                        if dative[0].pos_ == "NOUN":
                            process.actor = create_actor(dative[0])
                        elif dative[0].pos_ == "ADP":
                            pobj = find_dependency(["pobj"], token=dative[0])
                            if len(pobj) > 0:
                                process.actor = create_actor(pobj[0])
            elif process.actor.token.pos_ == "PRON" and process.action.token.dep_ == "relcl":
                new_actor = next(process.action.token.ancestors)
                if new_actor is not None:
                    process.actor = create_actor(new_actor)


def complement_object(container: SentenceContainer):
    """
    if the object in an action is a pronoun, it is possible that this action is a subordinate clause and the real object
    is in the main clause, this function tries to find the real object and add it to the action

    Args:
        container: The container that contains the action.
    """
    for process in container.processes:
        if process.action is not None:
            if process.action.object is None:
                return

            elif process.action.object.token.pos_ == "PRON":
                if process.action.token.dep_ == "relcl":
                    new_obj = next(process.action.token.ancestors)
                    if new_obj is not None:
                        process.action.object = Resource(new_obj)
                        return


def find_xcomp_ancestor(token):
    """
    find the xcomp ancestor of a token. If a token has no dependency of xcomp but conj, xcomp is perhaps
    in its conjunctions
    Args:
        token: spacy token object

    Returns:
        if xcomp is found, retuen its token, otherwise None.

    """
    if token.dep_ == "xcomp":
        return next(token.ancestors)

    if token.dep_ == "conj":
        return find_xcomp_ancestor(next(token.ancestors))
    else:
        return None


def belongs_to_action(container: SentenceContainer, token: Token):
    """
    Given a token, the function finds whether the token belongs to an action in the container
    Args:
        container: The container that contains the action.
        token: a spacy token object

    Returns:
        if a token belongs to an action, return the action, otherwise None
    """
    for process in container.processes:
        if process.action is not None:
            if process.action.token == token:
                return process
    return None
