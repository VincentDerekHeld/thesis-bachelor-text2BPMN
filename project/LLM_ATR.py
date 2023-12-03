import os
import requests
import spacy

from project.Constant import DEBUG, resolve_enumeration, filter_irrelevant_information, transform_implicit_actions
from project.Utilities import write_to_file, open_file


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
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    debug_mode = True #TODO: change to DEBUG
    doc = nlp(text_input)  # Create doc object from input text for identification of listings and for sentence splitting

    text_contains_listings = False
    if resolve_enumeration:
        for token in doc:
            if token.tag_ == "LS":
                print(f"Found listing: {token.text}")
                text_contains_listings = True
                break

    intro = """
    #### Intro: ###
    You carefully follow the instructions. 
    You solve the tasks step by step keeping as many words from the input text as possible, and never add information from the examples to the output.\n"""
    outro = """\n ### TEXT ### \n"""
    answer_outro = "\n ### Answer / Response: ###"

    prompts = []
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
    1) Decide carefully based on the provided background if a part of the following sentence fulfills the conditions of the provided background information. If the condition is fulfilled, go to 2), else go to 3).
    2) Filter carefully the information, that fulfills the condition, from the text (but sill return full sentences) or if the sentence consists only out of this irrelevant information return an empty message (just a spaces without any other characters).
    3) Return the text carefully without any changes or interpretations.
    """

    if filter_irrelevant_information: prompts.append(""" 
    ### Background Information: ###
    Introduction sentence that describe the company are not relevant and must be filtered.
        Example: The Sentence "A small company manufactures customized bicycles." must be filtered.
        Example: The Sentence "The Evanstonian is an upscale independent hotel." must be filtered.
    """ + filter_outro)

    if filter_irrelevant_information: prompts.append(""" 
    ### Background Information: ###
    Some parts of sentences just name the start of a process (instance) and are not relevant and must be filtered.
    Example: "Whenever the sales department receives an order, a new process instance is created." 
    -> "a new process instance is created." must be filtered. ->  "The sales department receives an order." must be returned.


    """ + filter_outro)

    if filter_irrelevant_information: prompts.append(""" 
    ### Background Information: ###
    Information that describes the outcome or the goal of the process or an activity are not relevant and must be filtered.
                Example: "to ensure valid results." this part must be filtered.
                Example: "to ensure that the audit programme(s) are implemented and maintained." this part must be filtered.
                Example: "as evidence of the results." this part must be filtered. 
                Example: "that are relevant to the information security management system" this part must be filtered.
                Example: "to ensure that the audit programme(s) are implemented and maintained." this part must be filtered.
    """ + filter_outro)

    # TODO: maybe those parts can be combined
    if filter_irrelevant_information: prompts.append(""" 
    ### Background Information: ###
    Information that describes the decision criteria for methods or techniques are not relevant and must be filtered.
                Example: "The methods selected should produce comparable and reproducible results to be considered valid;" must be filtered.
                    -> The sentence consists only out of this irrelevant information and an empty message must be returned.
                Example: "Eighty percent of room-service orders include wine or some other alcoholic beverage." must be filtered.
    """ + filter_outro)

    if filter_irrelevant_information: prompts.append(""" 
    ### Background Information: ###
    Information that clarifies that something is not universally applicable are not relevant and must be filtered.
                Examples: "as applicable", "if applicable", "where applicable", "where feasible" must be filtered.
       """ + filter_outro)

    if filter_irrelevant_information: prompts.append(""" 
    ### Background Information: ###
    Sentence parts that contain examples are not relevant and must be carefully filtered from the sentence.
                Example of key words:  parts containing "for example ...", "e.g. ..." must be filtered.
    """ + filter_outro)

    if filter_irrelevant_information: prompts.append(""" 
    ### Background Information: ###
        References to other Articles or Paragraphs are not relevant and must be filtered.
                Example: "referred to in Article 22(1) and (4)" must be filtered.
                Example: "in accordance with Article 55" must be filtered.
    """ + filter_outro)

    # Transform implicit actions into explicit actions
    if transform_implicit_actions: prompts.append("""
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
        3) Do not comment on this step and return carefully the full input sentence without any changes and interpretations.""")

    def generate_response(prompt: str) -> str:
        """
        Generate a response from the OpenAI API based on the provided prompt.
        Args:
            prompt: the prompt to generate a response from
        Returns:
            response_text: the generated response text
        """
        try:
            if debug_mode: print(f"*** Prompt: *** len: {len(prompt).__str__()} \n {prompt} \n")
            api_key = os.environ["OPENAI_API_KEY"]
            # Define the headers for the HTTP request
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            # Define the data payload for the API request
            data = {
                "model": "gpt-3.5-turbo-instruct",
                "prompt": prompt,
                "max_tokens": 1000,
                "temperature": 0
            }
            # Make the POST request to the OpenAI API
            response = requests.post('https://api.openai.com/v1/completions', headers=headers, json=data)
            # Extract the response text
            response_data = response.json()
            if response_data['choices']:
                response_text = response_data['choices'][0]['text'].strip()
            else:
                raise ValueError("No LLM response received in data")

            # response_text = response_text.strip()
            if debug_mode:
                print(f"*** LLM Response: ***\n {response_text}")
                print("*" * 50)

            return response_text

        except requests.exceptions.Timeout:
            raise TimeoutError("Request timed out while calling the OpenAI API")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")

    result = ""
    generate_response(inital_prompt + doc.text)
    if debug_mode: print(f"Text contains listings: {text_contains_listings}")
    if text_contains_listings:  #
        new_text = generate_response(prompt_enumeration_resolution + outro + doc.text + answer_outro)
        nlp = spacy.load('en_core_web_trf')
        doc = nlp(new_text)  # replace doc with old text with doc with new text, where listings are resolved

    for number, sent in enumerate(doc.sents):
        current_sent: str = sent.text
        # if current_sent.isspace() or current_sent.__len__() == 0:
        #   print(f"Skipped Sent No. {number} because it consists only of whitespace.")
        #  next(doc.sents)
        for prompt in prompts:
            if current_sent.isspace() or current_sent.__len__() == 0:
                if debug_mode: print(f"Sent No. {number} has been returned as empty message.")
                next(doc.sents)
                break  # TODO: check if this is correct
            # intro
            query = prompt + outro + current_sent + answer_outro
            current_sent = generate_response(query)
        result = result + " " + current_sent + "\n"
    result = result.strip()
    if debug_mode: print("**** Full description: **** \n" + result.replace("\n", " "))
    write_to_file(result, f"/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent/evaluation/LLM_ATR_results/{title}.txt") #TODO: change path, if DEBUG:
    return result


if __name__ == '__main__':
    """
    This method is used to run the LLM-assisted refinement without creating diagrams.
    """
    for i in range(1, 23):
        input_path = f"/text2BPMN-vincent/evaluation/golden_standard/Text{i}.txt"
        text_input = open_file(input_path)
        title = f"Text{i}_LLM_preprocessed_text"
        nlp = spacy.load('en_core_web_trf')
        LLM_assisted_refinement(text_input, nlp, title)
