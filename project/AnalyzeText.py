from spacy.matcher import Matcher
import Constant
from spacy import Language
from Model.Action import LinkType
from Model.Process import Process
from Model.SentenceContainer import SentenceContainer
from Structure.Activity import Activity
from Structure.Block import ConditionBlock, AndBlock, ConditionType
from Structure.Structure import LinkedStructure, Structure
from Utilities import find_dependency, find_action, contains_indicator, find_process
from WordNetWrapper import hypernyms_checker, verb_hypernyms_checker


def determine_marker(container: SentenceContainer, nlp: Language):
    """
    Determines the marker of the action in the given container.

    Args:
        container: The container that contains the action.
        nlp: The nlp language object.

    """
    determine_single_marker(container)
    determine_compound_marker(container, nlp)
    determine_jump_case_marker(container, nlp)


def determine_single_marker(container: SentenceContainer):
    """
    Determines the marker of the action that is composed of one word in the given container.

    Args:
        container: The container that contains the action.

    """
    mark_list = find_dependency(["mark"], sentence=container.sentence)
    for mark in mark_list:
        verb = next(mark.ancestors)
        if verb.pos_ == "PART":
            verb = next(verb.ancestors)
        action = find_action(verb, container)
        if action is not None:
            if mark.text.lower() in Constant.SINGLE_IF_CONDITIONAL_INDICATORS:
                action.marker = "if"
            elif mark.text.lower() in Constant.SINGLE_ELSE_CONDITIONAL_INDICATORS:
                action.marker = "else"
            elif mark.text.lower() == "that":
                if verb.dep_ == "ccomp":
                    main_clause = find_action(next(verb.ancestors), container)
                    if main_clause is not None:
                        sub_clause = find_action(verb, container)
                        sub_clause_process = find_process(container, action=sub_clause)
                        main_clause.subclause = sub_clause_process
                        container.processes.remove(sub_clause_process)

    advmod_list = find_dependency(["advmod"], sentence=container.sentence)
    for advmod in advmod_list:
        verb = next(advmod.ancestors)
        action = find_action(verb, container)
        if action is not None:
            if advmod.text.lower() in Constant.SINGLE_PARALLEL_INDICATORS:
                action.marker = "while"
            elif advmod.text.lower() in Constant.SINGLE_IF_CONDITIONAL_INDICATORS:
                action.marker = "if"
            elif advmod.text.lower() in Constant.SINGLE_ELSE_CONDITIONAL_INDICATORS:
                action.marker = "else"
            elif advmod.text.lower() in Constant.SINGLE_SEQUENCE_INDICATORS:
                action.marker = "then"

    prep_list = find_dependency(["prep"], sentence=container.sentence)
    for prep in prep_list:
        verb = next(prep.ancestors)
        action = find_action(verb, container)
        if action is not None:
            action.prep = prep


def determine_compound_marker(container: SentenceContainer, nlp: Language):
    """
    Determines the marker of the action that is composed of multiple words in the given container.

    Args:
        container: The container that contains the action.
        nlp: The nlp language object.

    """
    for process in container.processes:
        if process.action is None:
            continue

        if process.action.marker is not None:
            continue

        if contains_indicator(Constant.COMPOUND_CONDITIONAL_INDICATORS, process.sub_sentence, nlp):
            process.action.marker = "if"
        elif contains_indicator(Constant.COMPOUND_PARALLEL_INDICATORS, process.sub_sentence, nlp):
            process.action.marker = "while"
        elif contains_indicator(Constant.COMPOUND_SEQUENCE_INDICATORS, process.sub_sentence, nlp):
            process.action.marker = "then"


def determine_jump_case_marker(container: SentenceContainer, nlp: Language):
    """
    Determines whether the sentence contains an "in former/ latter case" expression. If so, mark that action as a
    jump case, which should later be added to a gateway

    Args:
        container: The container that contains the action.
        nlp: The nlp language object.

    """
    for process in container.processes:
        if process.action is None:
            continue

        matcher = Matcher(nlp.vocab)
        for rule in Constant.CASE_INDICATORS:
            for k, v in rule.items():
                matcher.add(k, [v])

        matches = matcher(process.sub_sentence)
        if len(matches) > 0:
            for match_id, start, end in matches:
                matched_span = process.sub_sentence[start:end]
                sent = matched_span.text
                if "former" in sent.lower():
                    process.action.link_type = LinkType.TO_PREV
                elif "latter" in sent.lower():
                    process.action.link_type = LinkType.TO_NEXT


def correct_order(container: [SentenceContainer]):
    """
    correct the sentence order in the container, the reason for this see the example below:
    # stop the maneuver if the pressure is too high -> if the pressure is too high, stop the maneuver

    Args:
        container: The container that contains the action.
    """

    for sentence in container:
        for process in sentence.processes:
            if process.action is None:
                continue

            if process.action.marker == "if":
                if not sentence.process_is_first(process):
                    # stop the maneuver if the pressure is too high -> if the pressure is too high, stop the maneuver
                    # swap the process with the other process that is before it in the container.processes list
                    index = sentence.processes.index(process)
                    sentence.processes.remove(process)
                    sentence.processes.insert(index - 1, process)


def remove_redundant_processes(container: [SentenceContainer]):
    """
    Remove the processes that are redundant in context of BPMN modeling. three cases are considered:
    1. The one whose action is None
    2. The one whose action is "be" and has no adjective or attribute
    3. The one who describes "have to do something"
    3. The one who simply describes the start of the process

    Args:
        container: The container that contains the action.
    """
    for sentence in container:
        for i in range(len(sentence.processes) - 1, -1, -1):
            if sentence.processes[i].action is None:
                sentence.processes.remove(sentence.processes[i])
            elif sentence.processes[i].action.token.pos_ == "AUX":
                sentence.processes.remove(sentence.processes[i])
            elif sentence.processes[i].action.token.lemma_ in ["consist", "include"]:
                sentence.processes.remove(sentence.processes[i])
            elif sentence.processes[i].action.token.lemma_ == "be":
                acomp = find_dependency(["acomp", "attr"], token=sentence.processes[i].action.token)
                if len(acomp) == 0:
                    sentence.processes.remove(sentence.processes[i])
            elif sentence.processes[i].action.token.lemma_ == "have":
                xcomp = find_dependency(["xcomp"], token=sentence.processes[i].action.token)
                if len(xcomp) > 0:
                    sentence.processes.remove(sentence.processes[i])
            elif describe_process_start(sentence.processes[i]):
                sentence.processes.remove(sentence.processes[i])


def describe_process_start(process: Process):
    """
    Determine whether the process describes the start of the process. This is achieved by checking whether the verb and
    it's hypernym has the meaning of "begin" and the actor has the meaning of "activity"
    Args:
        process: The process to be checked.

    Returns:
        true if the process describes the start of the process, false otherwise.

    """
    if process.actor is None:
        return False
    else:
        if hypernyms_checker(process.actor.token, ["activity"]) and \
                verb_hypernyms_checker(process.action.token, ["begin"]):
            return True
    return False


def determine_end_activities(structure_list: [Structure]):
    """
    determine whether an activity is an end activity. there are two cases:
    1. the last activity in the list is an end activity
    2. If the verb of an activity or its hypernyms has meaning of "end" and the actor or its hypernyms has meaning of
     "event", then it is an end activity
    3. If the verb of an activity or its hypernyms has meaning of "refuse" and the object or its hypernyms has meaning
     of "message", then it is an end activity
    Args:
        structure_list: the list of structures that contains the activities.
    """
    for structure in structure_list:
        if structure_list.index(structure) == len(structure_list) - 1:
            structure.is_end_activity = True
        elif isinstance(structure, ConditionBlock):
            for branch in structure.branches:
                for activity in branch["actions"]:
                    if activity.process.action.active:
                        actor = activity.process.actor
                    else:
                        actor = activity.process.action.object
                    if actor is not None:
                        if hypernyms_checker(actor.token, ["event"]) and \
                                verb_hypernyms_checker(activity.process.action.token, ["end"]):
                            activity.is_end_activity = True
                            continue
                        elif activity.process.action.object is not None and \
                                hypernyms_checker(activity.process.action.object.token, ["message"]) and \
                                verb_hypernyms_checker(activity.process.action.token, ["refuse"]):
                            activity.is_end_activity = True


def construct(container_list: [SentenceContainer]):
    """
    given the container list, the function will convert the corresponding container into the right structure (activity of gateway)
    Args:
        container_list: the list of containers that contains the actions.

    Returns:
        the constructed structure list.
    """
    result = []
    for i in range(len(container_list)):
        container = container_list[i]

        if container.has_if() or container.has_else():
            if last_container_has_conditional_marker(container, container_list):
                if isinstance(result[-1], ConditionBlock):
                    if result[-1].can_be_added(container):
                        result[-1].add_branch(container)
                    else:
                        if_block = ConditionBlock()
                        if_block.add_branch(container)
                        result.append(if_block)
            else:
                if_block = ConditionBlock()
                if_block.add_branch(container)
                result.append(if_block)

        elif container.has_while():
            if isinstance(result[-1], AndBlock):
                result[-1].add_branch(container)
            elif not isinstance(result[-1], ConditionBlock):
                and_block = AndBlock()
                and_block.add_branch(result[-1])
                and_block.add_branch(container)
                result.remove(result[-1])
                result.append(and_block)

        elif container.has_or():
            if_block = ConditionBlock()
            for process in container.or_processes:
                branch = {"type": ConditionType.ELSE, "condition": [], "actions": [Activity(process)]}
                if_block.branches.append(branch)
            result.append(if_block)

        else:
            result.append(container)

    return result


def build_flows(container_list: [SentenceContainer]):
    """
    given the container list, the function will convert the corresponding container into the
    right structure (activity of gateway) and perform some minor adjustments to the structure.
    Args:
        container_list: the list of containers that contains the actions.

    Returns:
        the constructed structure list.
    """
    flow_list = construct(container_list)
    result = []
    last_gateway = None

    for i in range(len(flow_list)):
        if isinstance(flow_list[i], ConditionBlock):
            last_gateway = flow_list[i]
            if not flow_list[i].is_complete():
                flow_list[i].create_dummy_branch()
            result.append(flow_list[i])
        elif isinstance(flow_list[i], AndBlock):
            last_gateway = flow_list[i]
            result.append(flow_list[i])
        else:
            for process in flow_list[i].processes:
                if process.action.link_type == LinkType.TO_PREV:
                    if last_gateway is not None:
                        last_gateway.add_to_branch(1, process)
                elif process.action.link_type == LinkType.TO_NEXT:
                    if last_gateway is not None:
                        last_gateway.add_to_branch(0, process)
                else:
                    result.append(Activity(process))

    return result


def build_linked_list(container_list: [SentenceContainer]):
    flow_list = construct(container_list)
    link = LinkedStructure()

    for i in range(len(flow_list)):
        if isinstance(flow_list[i], ConditionBlock):
            link.add_structure(flow_list[i])
        elif isinstance(flow_list[i], AndBlock):
            link.add_structure(flow_list[i])
        else:
            for process in flow_list[i].processes:
                activity = Activity(process)
                link.add_structure(activity)

    return link


def get_valid_actors(container_list: [SentenceContainer]) -> list:
    """
    iterate the container list and get all the actors that are real actors

    Args:
        container_list: The container that contains the action.

    Returns:
        A list of actors that are real actors.

    """
    result = []
    for container in container_list:
        for process in container.processes:
            if process.actor is not None:
                if process.actor.is_real_actor and process.actor.full_name not in result:
                    result.append(process.actor.full_name)

    return result


def adjust_actor_list(valid_actors: [str]) -> list:
    result = []
    add = True
    for i in range(len(valid_actors)):
        for j in range(len(valid_actors)):
            if i != j:
                if valid_actors[i] in valid_actors[j]:
                    add = False
                    break
        if add:
            result.append(valid_actors[i])
        else:
            add = True

    return result


def last_container_has_conditional_marker(container: SentenceContainer, container_list: [SentenceContainer]):
    """
    this function checks whether the last container has a conditional marker.
    Args:
        container: the container that is being checked.
        container_list: the list of containers.

    Returns:
        true if the last container has a conditional marker, false otherwise.
    """
    index = container_list.index(container)
    if index == 0:
        return False
    else:
        if container_list[index - 1].has_if() or container_list[index - 1].has_else():
            return True
        else:
            return False
