import spacy
import coreferee
import benepar
from spacy_wordnet.wordnet_annotator import WordnetAnnotator

import BPMNStarter
from project.Constant import DEBUG

if __name__ == '__main__':
    print("Start loading spacy model and adding components")
    nlp = spacy.load('en_core_web_trf')
    nlp_similarity = spacy.load("en_core_web_lg")
    if DEBUG:
        nlp.add_pipe('benepar', config={'model': 'benepar_en3'})
    else:
        nlp.add_pipe('benepar', config={'model': 'benepar_en3_large'})

    nlp.add_pipe("spacy_wordnet", after='tagger')
    nlp.add_pipe('coreferee')
    print("Finished loading spacy model and adding components")

    for i in range(1, 23):
        input_path = f"/Users/vincentderekheld/PycharmProjects/bachelor-thesis/Evaluation/text_input/Text{i}.txt"
        output_path = f"/Users/vincentderekheld/PycharmProjects/bachelor-thesis/Evaluation/baseline_yu/baseline_yu{i}.png"
        title = f"Text{i}_baseline_yu"
        print(f"Start generating model for {title}")
        try:
            BPMNStarter.start_task(nlp, nlp_similarity, input_path, title, output_path, debug=DEBUG)
        except Exception as e:
            print(f"Error for text {i}: {e}")
