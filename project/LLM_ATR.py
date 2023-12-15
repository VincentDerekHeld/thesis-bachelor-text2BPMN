import os
import requests
import spacy
from spacy.tokens import Doc

from project.Constant import DEBUG, resolve_enumeration, filter_irrelevant_information, transform_implicit_actions, \
    filter_finish_activities, BASE_PATH
from project.LLM_API import generate_response_GPT3_instruct_model, generate_response_GPT4_model
from project.Utilities import write_to_file, open_file, text_pre_processing


def contains_listings(doc: Doc) -> bool:
    text_contains_listings = False
    if resolve_enumeration:
        for token in doc:
            if token.tag_ == "LS":
                print(f"Found listing: {token.text}")
                text_contains_listings = True
                break
    return text_contains_listings


def LLM_assisted_refinement(text_input: str, nlp, title: str):
    """
    LLM-assisted refinement of the input text. The text refinement is based on the LLM model and includes the following steps:
    1) Resolve enumerations
    2) Filter irrelevant information
    3) Transform implicit actions into explicit actions

    Args:
        text_input: the input text to be refined
        nlp: the large spacy model
        title: the title of the text output diagram
    Returns:
        result: the LLM-assisted refined text
    """
    print("Start LLM-assisted refinement --- this can take some time...")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    debug_mode = True
    text_input = text_pre_processing(text_input)
    doc = nlp(text_input)  # Create doc object from input text for identification of listings and for sentence splitting
    outro = """\n ### TEXT ### \n"""
    answer_outro = "\n ### Answer / Response: ###"

    prompts_GPT3_instruct = []
    prompts_GPT4 = []
    inital_prompt = ("""
    ### Instruction: ###
    Read the text carefully and try to understand the content. 
    Return on this message an empty message (just a spaces without any other characters).
    ### Full Text ### \n""")

    prompt_enumeration_resolution = ("""
    ### Example: ###
    # Example Input: # 
    
    The actor shall determine:
    a) what needs to be done..
    b) the methods
    c) feedback on:
        1) the results
        2) monitoring

    # Example Output: # 
    The actor shall determine what needs to be done...
    The actor shall determine the methods...
    The actor shall determine feedback on the results, monitoring, 

    ### Instruction: ####
    Keep as many words from the original text as possible, and never add information (from the example) to the output. 
    Return the listings carefully transformed into a continuous text based on the example and filter the bullet points.

    """)

    # Relevance of Sentence
    filter_outro = """
    ### Instruction: ###
    Please never filter "in the meantime", "in the former case", "in the latter case" or conditions such as "if it is not available".
    1) Decide carefully based on the provided background if a part of the following sentence fulfills the conditions of the provided background information. If the condition is fulfilled, go to 2), else go to 3).
    2) Filter carefully the information, that fulfills the condition, from the text (but sill return full sentences) or if the sentence consists only out of this irrelevant information return an empty message (just a spaces without any other characters). 
    3) Return the text carefully without any changes or interpretations.
    """

    if filter_irrelevant_information: prompts_GPT3_instruct.append(""" 
    ### Background Information: ###
    Introduction sentence that describe the company are not relevant and must be filtered.
        Example: The Sentence "A small company manufactures customized bicycles." must be filtered.
        Example: The Sentence "The Evanstonian is an upscale independent hotel." must be filtered.
    """ + filter_outro)

    if filter_irrelevant_information: prompts_GPT3_instruct.append(""" 
    ### Background Information: ###
    Some parts of sentences just name the start of a process (instance) and are not relevant and must be filtered.
    Example: "Whenever the sales department receives an order, a new process instance is created." 
    -> "a new process instance is created." must be filtered. ->  "The sales department receives an order." must be returned.


    """ + filter_outro)

    if filter_irrelevant_information: prompts_GPT3_instruct.append(""" 
    ### Background Information: ###
    Information that describes the outcome or the goal of the process or an activity are not relevant and must be filtered.
                Example: "to ensure valid results." this part must be filtered.
                Example: "to ensure that the audit programme(s) are implemented and maintained." this part must be filtered.
                Example: "as evidence of the results." this part must be filtered. 
                Example: "that are relevant to the information security management system" this part must be filtered.
                Example: "to ensure that the audit programme(s) are implemented and maintained." this part must be filtered.
    """ + filter_outro)

    if filter_irrelevant_information: prompts_GPT3_instruct.append(""" 
    ### Background Information: ###
    Information that describes the decision criteria for methods or techniques are not relevant and must be filtered.
                Example: "The methods selected should produce comparable and reproducible results to be considered valid;" must be filtered.
                    -> The sentence consists only out of this irrelevant information and an empty message must be returned.
                Example: "Eighty percent of room-service orders include wine or some other alcoholic beverage." must be filtered.
    """ + filter_outro)

    if filter_irrelevant_information: prompts_GPT3_instruct.append(""" 
    ### Background Information: ###
    Information that clarifies that something is not universally applicable are not relevant and must be filtered.
                Examples: "as applicable", "if applicable", "where applicable", "where feasible" must be filtered.
       """ + filter_outro)

    if filter_irrelevant_information: prompts_GPT3_instruct.append(""" 
    ### Background Information: ###
    Sentence parts that contain examples are not relevant and must be carefully filtered from the sentence.
                Example of key words:  parts containing "for example ...", "e.g. ..." must be filtered.
    """ + filter_outro)

    if filter_irrelevant_information: prompts_GPT3_instruct.append(""" 
    ### Background Information: ###
        References to other Articles or Paragraphs are not relevant and must be filtered.
                Example: "referred to in Article 22(1) and (4)" must be filtered.
                Example: "in accordance with Article 55" must be filtered.
    """ + filter_outro)

    # Transform implicit actions into explicit actions
    if transform_implicit_actions: prompts_GPT3_instruct.append("""
    Extract implicit ACTIONS from the text and transform the Actions into explicit Actions.
                ## Examples: ##
                    #Example 1: The Sentence „Documented information shall be available as evidence of the implementation of the audit programme(s) and the audit results.“ must be transformed into „They shall document the information“ because it implies the ACTION „document the results“.
                    #Example 2: The Sentence "The Room Service Manager then submits an order ticket to the kitchen to begin preparing the food." must be transformed into „The Room Service Manager submits an order ticket to the kitchen. The kitchen prepares the food.“ and here it is importent to keep the order of the sentences and to explicitly name the ACTOR and the ACTION.
                 ### Instruction: ####
        Solve the tasks carefully step by step. Do not comment on any of the steps. Return the (transformed) sentence without interpretations.
        1) Analyze the following sentence to determine if a part contains any implicit actions. If it contains implicit actions go to 2), else go to 3). Do not comment on this step.
        2) If implicit action(s) are identified, these must be carefully transformed into explicit actions following the following conditions.
            1. Condition: The original structure and order of the sentence must be retained.
            2. Condition: The original wording of the sentence must be retained.
        3) Do not comment on this step and return carefully the full input sentence without any changes, quotation marks and interpretation.""")

    result = ""
    generate_response_GPT3_instruct_model(inital_prompt + doc.text)
    if debug_mode: print(f"Text contains listings: {contains_listings(doc)}")
    if contains_listings(doc):  #
        new_text = generate_response_GPT3_instruct_model(
            prompt_enumeration_resolution + outro + doc.text + answer_outro)
        nlp = spacy.load('en_core_web_trf')
        doc = nlp(new_text)  # replace doc with old text with doc with new text, where listings are resolved

    for number, sent in enumerate(doc.sents):
        current_sent: str = sent.text
        print(f"Input Current sentence: {current_sent}")
        for prompt in prompts_GPT3_instruct:
            if determine_if_empty_message(current_sent, number):
                next(doc.sents)
                break
            query = prompt + outro + current_sent + answer_outro
            current_sent = generate_response_GPT3_instruct_model(query)
            print(f"Output Current sentence: {current_sent}")
        for prompt in prompts_GPT4:
            if determine_if_empty_message(current_sent, number):
                next(doc.sents)
                break
            query = prompt + outro + current_sent + answer_outro
            current_sent = generate_response_GPT4_model(query)
            print(f"Output Current sentence: {current_sent}")
        result = result + " " + current_sent + "\n"
    result = result.strip()
    if debug_mode: print("**** Full description: **** \n" + result.replace("\n", " "))

    write_to_file(result, f"{BASE_PATH}/results/LLM_ATR_results/{title}.txt")
    f"/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent/evaluation/LLM_ATR_results2/{title}.txt"
    return result


def determine_if_empty_message(text: str, number) -> bool:
    """
    Determine if the text is an empty message.
    Args:
        text: the text to be analyzed
    Returns:
        True: if the text is an empty message
        False: if the text is not an empty message
    """
    if text.isspace() or text.__len__() == 0:
        print(f"Sent No. {number} has been returned as empty message.")
        return True
    else:
        return False


if __name__ == '__main__':
    """
    This method is used to run the LLM-assisted refinement without creating diagrams.
    """
    for i in range(1, 24):
        input_path = f"/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent/evaluation/gold_standard/Text{i}.txt"
        text_input = open_file(input_path)
        title = f"Text{i}_LLM_preprocessed_text"
        nlp = spacy.load('en_core_web_trf')
        LLM_assisted_refinement(text_input, nlp, title)
