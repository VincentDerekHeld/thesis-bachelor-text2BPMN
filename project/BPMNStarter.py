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


def download_all_dependencies():
    import nltk
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    benepar.download('benepar_en3')
    benepar.download('benepar_en3_large')
    nltk.download('wordnet')


def start_task(input_path, title, output_path, debug=False):
    os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = 'true'
    warnings.filterwarnings('ignore')
    # download_all_dependencies()

    nlp = spacy.load('en_core_web_trf')

    if debug:
        nlp.add_pipe('benepar', config={'model': 'benepar_en3'})
    else:
        nlp.add_pipe('benepar', config={'model': 'benepar_en3_large'})

    nlp.add_pipe("spacy_wordnet", after='tagger')
    nlp.add_pipe('coreferee')

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