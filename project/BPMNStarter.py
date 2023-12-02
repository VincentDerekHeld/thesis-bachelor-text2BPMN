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
from Utilities import text_pre_processing





def start_task(nlp,  nlp_similarity, input_path, title, output_path, debug=False):
    os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = 'true'
    warnings.filterwarnings('ignore')
    # download_all_dependencies()


    text_input = open(input_path, 'r').read().replace('\n', ' ')

    text_input = text_pre_processing(text_input)
    document = nlp(text_input)

    containerList = analyze_document(document)
    for container in containerList:
        determine_marker(container, nlp)
    correct_order(containerList)
    remove_redundant_processes(containerList)
    valid_actors = get_valid_actors(containerList)
    valid_actors = adjust_actor_list(valid_actors)

    flows = build_flows(containerList)
    determine_end_activities(flows)

    create_bpmn_model(flows, valid_actors, title, output_path)

    # print(build_linked_list(containerList))