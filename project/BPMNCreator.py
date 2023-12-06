from typing import Optional

from processpiper.text2diagram import render

from Structure.Activity import Activity
from Structure.Block import ConditionBlock, AndBlock, ConditionType
from Structure.Structure import Structure
from project.Constant import LLM_syntax_improval, resolve_first_lane_problem, resolve_syntax_problems
from project.LLM_ATR2 import improve_syntax, improve_syntax_tasks, improve_syntax_tasks2, improve_quality_of_task_labels


def create_bpmn_model(structure_list: [Structure], actor_list: list, title: str, save_path: str, text_description: str,
                      theme: str = "BLUEMOUNTAIN"):
    """
    Create a BPMN model from a list of structures and actors.
    Args:
        structure_list: the list of structures
        actor_list: the list of valid actors
        title: the title of the BPMN model
        save_path: the path to save the BPMN model
        theme: the theme of the BPMN model, default is BLUEMOUNTAIN
    """

    input_syntax_rule_based = create_bpmn_description(structure_list, actor_list, title, theme=theme)
    print(input_syntax_rule_based)
    if LLM_syntax_improval:
        try:
            render_bpmn_model(improve_syntax_tasks2(input_syntax_rule_based, text_description), save_path)
        except NotImplementedError as e:
            print(f"Error in create_bpmn_model: {e}")
            render_bpmn_model(input_syntax_rule_based, save_path)
    else:
        render_bpmn_model(input_syntax_rule_based, save_path)


def render_bpmn_model(input_syntax: str, path: str):
    """
    Render the BPMN model from the input syntax.
    Args:
        input_syntax: the generated input syntax
        path: the path to save the BPMN model

    """
    # TODO: Filter "as" in the input syntax to ensure: "invalid syntax" is not triggered
    render(input_syntax, path)


def create_bpmn_description(structure_list: [Structure], actor_list: list, title: str,
                            theme: str = "BLUEMOUNTAIN") -> str:
    """
    Create the input syntax for the BPMN model based on the list of structures and actors.
    construct the lanes according to the actors
    and then add the activities and gateways to the lanes according to the actor of the activity
    Args:
        structure_list: the list of structures
        actor_list: the list of valid actors
        title: the title of the BPMN model
        theme: the theme of the BPMN model, default is BLUEMOUNTAIN

    Returns:
        the constructed syntax for rendering the BPMN model
    """

    result = ""
    result += "title: " + title + "\n"
    result += "width: " + str(10000) + "\n"
    result += "colourtheme: " + theme + "\n"

    lanes = {}
    connections = []
    print(f"Actor List: {actor_list}")  # TODO: me
    # if len(actor_list) < 2: #TODO  this is wrong
    #   lanes["dummy"] = []
    # if actor = None -> dummy else actor
    # else:
    if resolve_first_lane_problem:
        for actor in actor_list:
            lanes[actor] = []
        if len(lanes) == 0:
            lanes["dummy"] = []
    else:
        if len(actor_list) < 2:
            lanes["dummy"] = []
            # if actor = None -> dummy else actor
        else:
            for actor in actor_list:
                lanes[actor] = []

    key = None
    connection_id = 0
    last_gateway = None
    for structure in structure_list:
        if structure_list.index(structure) == 0:
            key = belongs_to_lane(structure_list, lanes, structure, key)
            lanes[key].append("(start) as start")
            connections.append("start")

        if isinstance(structure, Activity):
            key = belongs_to_lane(structure_list, lanes, structure, key)
            append_to_lane(key, lanes, connection_id, connections, structure, last_gateway)
        elif isinstance(structure, ConditionBlock):
            end_gateway = "gateway_" + str(structure.id) + "_end"

            if len(structure.branches[0]["condition"]) > 0:
                key = belongs_to_lane(structure_list, lanes, structure.branches[0]["condition"][0], key)
            append_to_lane(key, lanes, connection_id, connections, structure, last_gateway)

            for branch in structure.branches:
                connection_id += 1
                if structure.is_simple() and branch["type"] == ConditionType.IF:
                    connections.append("gateway_" + str(structure.id) + '-"yes"')
                elif structure.is_simple() and branch["type"] == ConditionType.ELSE:
                    connections.append("gateway_" + str(structure.id) + '-"no"')
                else:
                    condition = ""
                    for c in branch["condition"]:
                        condition += str(c)
                        if branch["condition"].index(c) != len(branch["condition"]) - 1:
                            condition += ", "
                    index = 0
                    for i in range(len(condition)):
                        index += 1
                        if condition[i] == " " and index > 15:
                            condition = condition[:i] + "\\n" + condition[i + 1:]
                            index = 0
                    connections.append("gateway_" + str(structure.id) + '-"' + condition + '"')

                need_end_gateway = True
                for activity in branch["actions"]:
                    print(f"Case 103: Activity: {activity}, activity.is_end_activity: {activity.is_end_activity}")
                    key = belongs_to_lane(structure_list, lanes, activity, key)
                    append_to_lane(key, lanes, connection_id, connections, activity, last_gateway)
                    if activity.is_end_activity:
                        need_end_gateway = False
                        end_id = "end_" + str(activity.id)
                        early_end_gateway = "(end) as end_" + str(activity.id)
                        lanes[key].append(early_end_gateway)
                        connections[connection_id] += "->" + end_id
                        continue

                if need_end_gateway:
                    connections[connection_id] += "->" + end_gateway

            lanes[key].append("<> as " + end_gateway)
            connection_id += 1
            last_gateway = end_gateway
        elif isinstance(structure, AndBlock):
            end_gateway = "gateway_" + str(structure.id) + "_end"

            append_to_lane(key, lanes, connection_id, connections, structure, last_gateway)

            for branch in structure.branches:
                connection_id += 1
                connections.append("gateway_" + str(structure.id))
                for activity in branch:
                    key = belongs_to_lane(structure_list, lanes, activity, key)
                    append_to_lane(key, lanes, connection_id, connections, activity, last_gateway)
                connections[connection_id] += "->" + end_gateway

            lanes[key].append("<@parallel> as " + end_gateway)
            connection_id += 1
            last_gateway = end_gateway

        if structure.is_end_activity:
            lanes[key].append("(end) as end")
            if connection_id < len(connections):
                connections[connection_id] += "->end"
            else:
                connections.append(last_gateway)
                connections[connection_id] += "->end"

    for lane in lanes:
        if len(lanes[lane]) > 0:  # VH: added if statement
            if lane == "dummy":
                result += "lane: \n"
            else:
                # if len(lanes[lane]) > 0: #TODO evaluate if we should added if statement
                result += "lane: " + lane + "\n"

            for element in lanes[lane]:
                result += "\t" + element + "\n"

    result += "\n"

    for connection in connections:
        result += connection + "\n"

    return result


def create_activity_label(action, id, actor=None) -> str:
    """
    Create the activity label for the BPMN model. 
    Args:
        action: the action of the structure to be appended
        id: the id of the structure
        actor: the actor of the structure, if it is None, then the actor is not appended to the label
    Returns:
        str: the activity label
    """
    action_text = str(action)
    action_text = action_text.replace("as ", "")
    if actor is not None:
        """ "[" + str(structure.process.actor) + " " + str(structure.process.action) + "] as activity_" + str(structure.id) """
        return "[" + str(actor) + " " + action_text + "] as activity_" + str(id)
    else:
        """ "[" + str(structure.process.action) + "] as activity_" + str(structure.id) """
        return "[" + action_text + "] as activity_" + str(id)
    pass


def append_to_lane(key: str, lanes: {}, connection_id: int, connections: list, structure: Structure,
                   last_gateway: Optional[str]):
    """
    append the corresponding element to the lane that it belongs to
    Args:
        key:
        lanes: the dictionary that contains the lanes
        connection_id: the index of the connection that is being appended
        connections: the list of connections
        structure: the structure that is being appended
        last_gateway: the last gateway that was appended

    """
    if resolve_syntax_problems:
        if isinstance(structure, Activity):
            if structure.process.actor is not None:
                if structure.process.actor.full_name in lanes.keys():
                    lanes[key].append(create_activity_label(structure.process.action, structure.id))
                else:
                    lanes[key].append(create_activity_label(structure.process.action, structure.id, structure.process.actor))
            else:
                lanes[key].append(
                    create_activity_label(structure.process.action, structure.id))
        elif isinstance(structure, ConditionBlock):
            if structure.is_simple():
                condition = structure.branches[0]["condition"][0]
                if condition is not None:
                    lanes[key].append("<" + str(condition) + "?> as gateway_" + str(structure.id))
                else:
                    lanes[key].append("<> as gateway_" + str(structure.id))
            else:
                lanes[key].append("<> as gateway_" + str(structure.id))
        elif isinstance(structure, AndBlock):
            lanes[key].append("<@parallel> as gateway_" + str(structure.id))

        if isinstance(structure, Activity):
            connection_name = "activity_" + str(structure.id)
        else:
            connection_name = "gateway_" + str(structure.id)

        if connection_id > len(connections) - 1:
            if last_gateway is not None:
                connections.append(last_gateway)
                connections[connection_id] += "->" + connection_name
            else:
                connections.append(connection_name)
        else:
            connections[connection_id] += "->" + connection_name
    else:
        if isinstance(structure, Activity):
            if structure.process.actor is not None:
                if structure.process.actor.full_name in lanes.keys():
                    lanes[key].append("[" + str(structure.process.action) + "] as activity_" + str(structure.id))
                else:
                    lanes[key].append(
                        "[" + str(structure.process.actor) + " " + str(structure.process.action) + "] as activity_" +
                        str(structure.id))
            else:
                lanes[key].append(
                    "[" + str(structure.process.action) + "] as activity_" + str(structure.id))
        elif isinstance(structure, ConditionBlock):
            if structure.is_simple():
                condition = structure.branches[0]["condition"][0]
                if condition is not None:
                    lanes[key].append("<" + str(condition) + "?> as gateway_" + str(structure.id))
                else:
                    lanes[key].append("<> as gateway_" + str(structure.id))
            else:
                lanes[key].append("<> as gateway_" + str(structure.id))
        elif isinstance(structure, AndBlock):
            lanes[key].append("<@parallel> as gateway_" + str(structure.id))

        if isinstance(structure, Activity):
            connection_name = "activity_" + str(structure.id)
        else:
            connection_name = "gateway_" + str(structure.id)

        if connection_id > len(connections) - 1:
            if last_gateway is not None:
                connections.append(last_gateway)
                connections[connection_id] += "->" + connection_name
            else:
                connections.append(connection_name)
        else:
            connections[connection_id] += "->" + connection_name


def belongs_to_lane(activity_list: [Structure], lanes: {}, structure: Structure,
                    previous_actor: Optional[str]) -> str:
    if resolve_first_lane_problem:
        """
        This method is used to determine which lane the activity belongs to.
        Args:
            activity_list: the list of activities
            lanes: the dictionary of lanes
            structure: the current structure that is being processed
            previous_actor: the actor of the previous activity
    
        Returns:
            the name of the lane, if the lane has length 1, then it returns "dummy"
        """
        if len(lanes) == 1 and next(iter(lanes)) == "dummy":  # TODo: maybe delte this to lines
            return "dummy"

        if previous_actor is None:
            for activity in activity_list:
                if isinstance(activity, Activity):
                    if activity.process.actor is not None:
                        for key in lanes.keys():
                            if not " " in activity.process.actor.full_name:
                                if activity.process.actor.full_name in key:
                                    return key
                            else:
                                if activity.process.actor.full_name == key:
                                    return activity.process.actor.full_name
                    # else:
                    #   return "dummy"
        else:
            if structure.process.actor is None:
                return previous_actor
            else:
                if structure.process.actor.full_name in lanes.keys():
                    return structure.process.actor.full_name
                else:
                    return previous_actor
    else:
        if len(lanes) == 1:  # TODo: maybe delte this to lines
            return "dummy"

        if previous_actor is None:
            for activity in activity_list:
                if isinstance(activity, Activity):
                    if activity.process.actor is not None:
                        for key in lanes.keys():
                            if not " " in activity.process.actor.full_name:
                                if activity.process.actor.full_name in key:
                                    return key
                            else:
                                if activity.process.actor.full_name == key:
                                    return activity.process.actor.full_name
                    # else:
                    #   return "dummy"
        else:
            if structure.process.actor is None:
                return previous_actor
            else:
                if structure.process.actor.full_name in lanes.keys():
                    return structure.process.actor.full_name
                else:
                    return previous_actor
