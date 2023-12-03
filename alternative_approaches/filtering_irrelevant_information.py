def remove_introduction_sentence(doc: Doc, nlp_similarity, nlp) -> Doc:
    """
    @param doc: The document that should be checked for an introduction sentence.
    @param nlp_similarity: The nlp model that is used to check the similarity between the first sentence and the entire document.
    @param nlp: The nlp model that is used to reconstruct the document without the first sentence.
    @return: The document without the first sentence if it is an introduction sentence.

    This function removes the first sentence of the document if it is an introduction sentence.
    Introduction sentences are sentences that are not related to the main content of the document.
    This function uses the similarity between the first sentence and the entire document to determine if the first sentence is an introduction sentence.
    """
    doc_new = nlp_similarity(doc.text)
    sentences = list(doc_new.sents)
    # Check similarity between the first sentence and the entire document
    # print("Similarity: " + sentences[0].similarity(doc_new).__str__() + " for sentence: " + sentences[0].text)
    if sentences[0].similarity(doc_new) < 0.9:
        # print("First sentence is an introduction sentence")
        # If the condition is met, reconstruct the document without the first sentence
        new_text = ' '.join([sent.text for sent in sentences[1:]])
        doc = nlp(new_text)
    return doc
