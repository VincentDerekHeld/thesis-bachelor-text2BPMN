import os
import warnings

import spacy
import coreferee
import benepar
from spacy_wordnet.wordnet_annotator import WordnetAnnotator

import BPMNStarter
from project.Constant import DEBUG

if __name__ == '__main__':
    print("Start loading spacy model and adding components")
    os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = 'true'
    warnings.filterwarnings('ignore')

    nlp = spacy.load('en_core_web_trf')
    nlp_similarity = spacy.load("en_core_web_lg")
    if DEBUG:
        nlp.add_pipe('benepar', config={'model': 'benepar_en3'})
    else:
        nlp.add_pipe('benepar', config={'model': 'benepar_en3_large'})

    nlp.add_pipe("spacy_wordnet", after='tagger')
    nlp.add_pipe('coreferee')
    print("Finished loading spacy model and adding components")

    for i in range(1,24): # (m, n) -> m is inclusive, n is exclusive, for all (1, 24), for a single one (i, i+1)
        input_path = f"/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent/evaluation/LLM_ATR_results/text{i}_our_approach.txt"
        #input_path = f"/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent/evaluation/gold_standard/Text{i}.txt"
        title = f"text{i}_our_approach"  # Title has to be without spaces, use underscore instead
        output_path = f"/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent/evaluation/our_approach3/{title}.png"
        print(f"Start generating model for {title}")
        try:
            BPMNStarter.start_task(nlp, nlp_similarity, input_path, title, output_path)
        except Exception as e:
            print(f"Error for text {i}: {e}")
