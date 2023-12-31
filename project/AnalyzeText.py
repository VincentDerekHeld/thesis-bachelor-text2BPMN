from spacy.matcher import Matcher
import Constant
from spacy import Language
from Model.Action import LinkType
from Model.Process import Process
from Model.SentenceContainer import SentenceContainer
from Structure.Activity import Activity
from Structure.Block import ConditionBlock, AndBlock, ConditionType
from Structure.Structure import LinkedStructure, Structure
from Utilities import find_dependency, find_action, contains_indicator, find_process, contains_any
from WordNetWrapper import hypernyms_checker, verb_hypernyms_checker
from project.LLM_API import normalize_boolean_result, generate_response_GPT4_model


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


def determine_end_activities(structure_list: [Structure], text_input: str):
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
            # if Constant.filter_finish_activities:
            #   determine_finish_activity(structure)
            # print(f"structure.is_end_activity: {structure.is_end_activity} Case 1: {structure}")
        if isinstance(structure, Activity):
            if Constant.filter_finish_activities:
                determine_finish_activity(structure)
                if structure.is_finish_activity:
                    previous_structure = structure_list[structure_list.index(structure) - 1]
                    previous_structure.is_end_activity = True
        elif isinstance(structure, ConditionBlock):
            for branch in structure.branches:
                for activity in branch["actions"]:
                    if Constant.filter_finish_activities:
                        determine_finish_activity(activity)
                    if activity.process.action.active:
                        actor = activity.process.actor
                    else:
                        actor = activity.process.action.object
                    if actor is not None:
                        if hypernyms_checker(actor.token, ["event"]) and \
                                verb_hypernyms_checker(activity.process.action.token, ["end"]):
                            activity.is_end_activity = True
                            # print(f"activity.is_end_activity: {activity.is_end_activity} Case 2: {activity}")
                            continue
                        elif activity.process.action.object is not None and \
                                hypernyms_checker(activity.process.action.object.token, ["message"]) and \
                                verb_hypernyms_checker(activity.process.action.token, ["refuse"]):
                            activity.is_end_activity = True
                            # continue
                        elif Constant.filter_finish_activities and decide_if_end_of_process(
                                str(activity.process.action), text_input):
                            print(f"101: activity.process.action.token: {activity.process.action.token}")
                            print(f"101: activity.process.action.str: {str(activity.process.action)}")
                            activity.is_end_activity = True


def decide_if_end_of_process(activity: str, text_input: str) -> bool:
    debug_mode = True
    prompt = (f"""
    Please determine carefully based on the process description if the following activity can represents the end of a process. 
    Respond with "True" if it is the end of the process, or "False" if it is not. 
    Use the example as a guide: In the process of repairing a car, if the activity is "customer take car," then this activity signifies the end of the process.

    ### Activity: ###
    {activity}

    ### Full Text: ###
    {text_input}
    """)
    if contains_any(activity, Constant.NOT_END_ACTIVITY_VERBS):
        return False
    else:
        result = ""
        result = generate_response_GPT4_model(prompt)
        result = result.strip()
        print(f"prompt: Activity is End: {result}: {activity}")
        # if debug_mode: print("**** Full description: **** \n" + result.replace("\n", " "))
        result = normalize_boolean_result(result)
        return result


def remove_redundant_end_activities(structure_list: [Structure]):
    for structure in structure_list:
        if isinstance(structure, ConditionBlock):
            for branch in structure.branches:
                for activity in branch["actions"]:
                    if activity.is_finish_activity:
                        branch["actions"].remove(activity)
                        print(f"structure_list.remove(structure): {structure}")
        elif isinstance(structure, Activity):
            if structure.is_finish_activity:
                structure_list.remove(structure)
                print(f"structure_list.remove(structure): {structure}")


def determine_finish_activity(activity: Activity):
    if Constant.filter_finish_activities:
        if "finish the process" in str(activity.process.action):
            activity.is_finish_activity = True
            print(f"activity.is_finish_activity: {activity.is_finish_activity} Activity: {activity}")


def determine_end_activities_backup(structure_list: [Structure]):
    # THis is a backup function for the end activity determination
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


def get_valid_actors(container_list: [SentenceContainer], nlp) -> list:
    """
    iterate the container list and get all the actors that are real actors
    and checks if there are actors that are similar to each other, as they are the same actor but with different names
    Args:
        container_list: The container that contains the action.
    Returns:
        A list of actors that are real actors.
    """
    if Constant.actors_similarity:
        result = []
        for container in container_list:
            for process in container.processes:
                if process.actor is not None:
                    if process.actor.is_real_actor and process.actor.full_name not in result:
                        temp_bool_add = True
                        for actor in result:
                            if compare_actors_similarity(process.actor.determinate_full_name_vh(), actor, nlp):
                                temp_bool_add = False
                                process.actor.full_name = actor
                                break
                        if temp_bool_add:
                            result.append(process.actor.full_name)
        return result
    else:
        result = []
        for container in container_list:
            for process in container.processes:
                if process.actor is not None:
                    if process.actor.is_real_actor and process.actor.full_name not in result:
                        result.append(process.actor.full_name)

        return result


def compare_actors_similarity(Actor1: str, Actor2: str, nlp):
    criteria_similarity_score = 0.5
    criteria_similarity_ratio = 0.5
    similarity_score = compare_actors_with_similarity(Actor1, Actor2, nlp)
    similarity_ratio = compare_actors_with_token(Actor1, Actor2, nlp)
    result = similarity_score > criteria_similarity_score and similarity_ratio > criteria_similarity_ratio
    # print("Similarity{:<60}{:<60}{:<20}{:<10}{:<10}".format(result.__str__(), Actor1, Actor2, similarity_score, similarity_ratio))
    return result


def compare_actors_with_similarity(Actor1: str, Actor2: str, nlp):
    doc1 = nlp(Actor1)
    doc2 = nlp(Actor2)
    similarity_score = round(doc1.similarity(doc2), 2)
    return similarity_score


def compare_actors_with_token(Actor1: str, Actor2: str, nlp):
    # Process the actor names using spaCy
    doc1 = nlp(Actor1)
    doc2 = nlp(Actor2)

    # Filter out tokens where token.is_stop = True
    tokens1 = [token for token in doc1 if not token.is_stop]
    tokens2 = [token for token in doc2 if not token.is_stop]

    # Count the number of tokens for each actor
    num_tokens1 = len(tokens1)
    num_tokens2 = len(tokens2)

    # Initialize variables to count matching tokens
    matching_tokens = 0

    # Compare the tokens in the actor with fewer tokens with tokens in the other actor
    if num_tokens1 <= num_tokens2:
        for token1 in tokens1:
            for token2 in tokens2:
                if token1.lemma_ == token2.lemma_:
                    matching_tokens += 1
                    break  # Break the inner loop if a match is found
    else:
        for token2 in tokens2:
            for token1 in tokens1:
                if token2.lemma_ == token1.lemma_:
                    matching_tokens += 1
                    break  # Break the inner loop if a match is found

    # Calculate the average number of tokens between the two actors
    avg_tokens = (num_tokens1 + num_tokens2) / 2.0

    # Calculate the similarity ratio
    similarity_ratio = matching_tokens / avg_tokens if avg_tokens > 0 else 0.0

    # print("Similarity similarity_ratio:", similarity_ratio)
    return similarity_ratio


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
