import spacy
import warnings
import os
import coreferee
import benepar
from spacy_wordnet.wordnet_annotator import WordnetAnnotator

from AnalyzeSentence import analyze_document
from AnalyzeText import determine_marker, correct_order, build_flows, get_valid_actors, \
    remove_redundant_processes, determine_end_activities, adjust_actor_list
from BPMNCreator import create_bpmn_model
from Utilities import text_pre_processing, open_file
from alternative_approaches.filtering_irrelevant_information import remove_introduction_sentence
from project.Constant import LLM_ATR, remove_introduction_sentence_with_spacy
from LLM_ATR import LLM_assisted_refinement


def start_task(nlp, nlp_similarity, input_path, title, output_path):
    """
    This method is the entry point for the BPMN generation. It takes a text file as input and generates a BPMN model.
    Args:
        nlp: spacy model with larger vocabulary
        nlp_similarity: spacy model with vector similarity for similarity calculation
        input_path: path to text file
        title: title of the BPMN model
        output_path: output path for the BPMN model, containing the file name and file type (.png)
        debug: boolean value to determine if the debug mode should be activated
    Returns:
        None
    """
    text_input = open_file(input_path)
    if LLM_ATR: text_input = LLM_assisted_refinement(text_input, nlp, title)
    text_input = text_pre_processing(text_input)

    document = nlp(text_input)
    if remove_introduction_sentence_with_spacy: document = remove_introduction_sentence(document, nlp_similarity, nlp)
    containerList = analyze_document(document)
    for container in containerList:
        determine_marker(container, nlp)
    correct_order(containerList)
    remove_redundant_processes(containerList)
    # valid_actors = get_valid_actors(containerList)
    valid_actors = get_valid_actors(containerList, nlp_similarity)
    valid_actors = adjust_actor_list(valid_actors)
    flows = build_flows(containerList)
    determine_end_activities(flows)
    create_bpmn_model(flows, valid_actors, title, output_path, text_input)
