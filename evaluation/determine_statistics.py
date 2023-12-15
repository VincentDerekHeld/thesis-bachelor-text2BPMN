import spacy
from spacy.pipeline.dep_parser import Language


def print_all_texts(input: str, text_number):
    print("Text: " + text_number.__str__() + "\n"
          + input + "\n")


def number_of_sentences():
    itaration = 1
    while itaration < 24:
        input_path = "/Users/vincentderekheld/PycharmProjects/bachelor-thesis/project/Text/text_input_vh/Text" + itaration.__str__() + ".txt"
        text_input = open(input_path, 'r').read().replace('\n', ' ')
        nlp = spacy.load('en_core_web_trf')
        doc = nlp(text_input)
        number_of_sentences = len(list(doc.sents))
        print(f"Text{itaration.__str__()}: {number_of_sentences}")
        itaration += 1


def number_of_tokens():
    itaration = 1
    while itaration < 24:
        input_path = "/Users/vincentderekheld/PycharmProjects/bachelor-thesis/project/Text/text_input_vh/Text" + itaration.__str__() + ".txt"
        text_input = open(input_path, 'r').read().replace('\n', ' ')
        nlp = spacy.load('en_core_web_trf')
        doc = nlp(text_input)
        number_of_tokens = len(list(doc))
        print(f"Text{itaration.__str__()}: {number_of_tokens}")
        itaration += 1


def splitting_test():
    input_path = "/Evaluation/text_input_vh/Text5.txt"
    text_input = open(input_path, 'r').read().replace('\n', ' ')
    nlp = spacy.load('en_core_web_trf')

    @Language.component("custom_sentencizer")
    def custom_sentencizer(doc):
        """Custom sentencizer that sets 'LS' tokens as sentence starts. It is added to the pipeline before the parser.
           Here, it is not added, because the LLM resolves the problem with a higher quality."""
        for token in doc:
            if token.tag_ == "LS":
                token.is_sent_start = True
        return doc

    # Register the custom sentencizer and add it to the pipeline before the parser
    nlp.add_pipe("custom_sentencizer", before="parser")
    doc = nlp(text_input)
    for sent in doc.sents:
        print(f" Sentence: {sent.text}")


splitting_test()
