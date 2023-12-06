from project.LLM_API import generate_response_GPT3_instruct_model, normalize_boolean_result, \
    generate_response_GPT4_model
from project.Structure.Block import ConditionBlock
from project.Structure.Structure import Structure


def decide_if_end_of_process(activity: str, text_input: str) -> bool:
    debug_mode = True
    prompt = (f"""
    Determine if the following activity represents the end of a process as described in the full text. 
    Respond with "True" if it is the end of the process, or "False" if it is not. 
    Use the example as a guide: In the process of repairing a car, if the activity is "customer take car," then this activity signifies the end of the process.

    ### Activity: ###
    {activity}

    ### Full Text: ###
    {text_input}
    """)
    print(f"prompt: {prompt}")
    result = ""
    result = generate_response_GPT4_model(prompt)
    result = result.strip()
    if debug_mode: print("**** Full description: **** \n" + result.replace("\n", " "))
    result = normalize_boolean_result(result)
    return result


def decide_if_end_of_process1(text_input: str) -> bool:
    debug_mode = True
    prompt = (f"""
    If yes, return only "True", otherwise return only "False".
    Carefully determine if the following text describes the end of a process:
    ### Text: ###
    {text_input}
    """)
    result = ""
    result = generate_response_GPT3_instruct_model(prompt)
    result = result.strip()
    if debug_mode: print("**** Full description: **** \n" + result.replace("\n", " "))
    result = normalize_boolean_result(result)
    return result


def use_decide_if_end_of_process(structure_list: [Structure], text_input: str):
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
        print(structure)
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
                        print(decide_if_end_of_process(activity.process.action.token, text_input))


if __name__ == '__main__':
    # decide_if_end_of_process("finish the process instance")
    print("Hello, World!")
