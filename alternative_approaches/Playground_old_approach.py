import spacy

nlp = spacy.load("en_core_web_lg")
version = nlp.meta["version"]
print(f"en_core_web_lg version: {version}")

causal_identifier_textual = ["whenever", "if", "whether", "in case of", "in the case of"]
causal_identifier_dependency = ["advcl", "advmod", "mark", "mark", "mark"]

XOR_criteria = ["or"]
AND_criteria = ["and", "in the meantime"]


def is_condtional(sent) -> bool:
    for token in sent:
        if (token.dep_ == "mark" or "advcl") and (token.text.lower() in causal_identifier_textual):
            return True
    return False


def is_active(token_root) -> bool:
    for token in token_root.children:
        if token.dep_ == "nsubj":
            if token.head.pos_ == "VERB":
                return True
    return False


def is_active1(sent) -> bool:
    """
    description: Checks if the main clause is active
    :param sent: Sentence that needs to be checked
    :return: boolean with True if main clause is active, False if not
    """
    for token in sent.root.children:
        if token.dep_ == "nsubj" and token.head.pos_ == "VERB":
            return True
    return False


def determine_condition(sent_root):  # sent_root = assamble
    active = True
    print("determine_condition:", active, sent_root.text)
    full_name_tokens = []
    for token in sent_root.children:
        if active:
            if token.dep_ == "advcl":  # token = reserved
                full_name_tokens = extract_from_active_sentence(token)
        elif not active:
            for token1 in token.children:
                if (token1.dep_ == "cc" and token1.text in AND_criteria):  # token1 = and
                    full_name_tokens.append(token1)
                    for token2 in token.children:
                        if token2.dep_ == "conj" and (token2.pos_ == "VERB" or token2.pos_ == "AUX"):
                            full_name_tokens.extend(determinate_full_verb(token2))
            sorted_tokens = sorted(full_name_tokens, key=lambda token: token.i)
            full_name_tokens = sorted_tokens
    return full_name_tokens


def extract_elements(sentence, process):
    """
    extract the elements from the sentence, creating the corresponding models, and adding them to the processes

    Args:
        sentence: the complete sentence
        process: the process where the elements should be determined and then be added to
        nlp: the spacy language model
    """
    sentence_is_active = is_active(sentence)

    actor = determine_actor(sentence, sentence_is_active)
    process.actor = create_actor(actor)

    verb = determine_predicate(sentence, sentence_is_active)
    obj = determine_object(verb, sentence_is_active)
    process.action = create_action(verb, obj)

    if process.action is not None:
        process.action.active = sentence_is_active
        for conjunct in process.action.token.conjuncts:
            if conjunct == process.action.token:
                continue
            if sentence.start < conjunct.i < sentence.end:
                conjunct_obj = determine_object(conjunct, sentence_is_active)
                conjunct_action = create_action(conjunct, conjunct_obj)
                process.action.conjunction.append(conjunct_action)


def extract_from_active_sentence(sent_root, conditonal=False) -> []:
    """
    This method is used, whenever a verb is found in the sentence. The first sent_root is the root of the main clause.
    :param sent_root: Token that represents the root of the clause
    :return:
    """
    final_tasks = []
    temp_task = Task()
    temp_action_tokens = determinate_full_verb(sent_root)
    temp_task.verb = temp_action_tokens
    actions.append(tokens_to_string(temp_action_tokens))

    if conditonal:
        temp_XOR = XOR()
        temp_XOR.decision_criteria = determine_condition(sent_root)

    for token in sent_root.children:
        # Find all nsubj = actors
        if token.dep_ == "nsubj":
            actors.append(tokens_to_string(determinate_full_name(token)))
            temp_task.actors = determinate_full_name(token)

        # Find all dobj = objects
        if token.dep_ == "dobj":
            objects.append(tokens_to_string(determinate_full_name(token)))
            temp_task.object = determinate_full_name(token)

        # check if verb has a prep
        if token.dep_ == "prep":
            helpers.append(tokens_to_string(determinate_full_name(token)))
            temp_task.helper = determinate_full_name(token)

        # verb or verb sentence
        if token.dep_ == "cc" and token.text in XOR_criteria:
            if isinstance(temp_task, XOR):
                print("Warning: already XOR")
            else:
                temp_XOR = XOR()
                temp_XOR.tasks.append(temp_task)
                for token1 in sent_root.children:
                    if token1.dep_ == "conj" and token1.pos_ == "VERB":
                        temp_XOR.tasks.extend(extract_from_active_sentence(token1))
                temp_task = temp_XOR

        # verb and verb sentence
        if (token.dep_ == "cc" and token.text in AND_criteria):
            temp_AND = AND()
            temp_AND.tasks.append(temp_task)
            for token1 in sent_root.children:
                if token1.dep_ == "conj" and token1.pos_ == "VERB":
                    temp_AND.tasks.extend(extract_from_active_sentence(token1))
            temp_task = temp_AND

    if conditonal:
        temp_XOR.tasks.append(temp_task)
        final_tasks.append(temp_XOR)
        # print("Return XOR: ", temp_XOR.__str__() + "\n")
    else:
        final_tasks.append(temp_task)
    # print("extract_from_active_sentence: End ", temp_task.__str__())
    return final_tasks


def extract_from_passive_sentence(sent_root, conditional=False):
    print("***Warning: passive sentence***", sent_root.sent.text)
    final_tasks = []
    temp_task = Task()
    temp_action_tokens = determinate_full_verb(sent_root)
    actions.append(tokens_to_string(temp_action_tokens))
    temp_task.verb = temp_action_tokens

    if conditional:
        temp_XOR = XOR()
        temp_XOR.decision_criteria = determine_condition(sent_root)

    print("extract_from_passive_sentence: ", sent_root.text, sent_root.dep_, sent_root.pos_)
    for token in sent_root.children:
        if token.dep_ == "auxpass":
            for subtoken in token.children:
                if subtoken.dep_ == "nsubjpass" or "nsubj":
                    temp_task.object = determinate_full_name(subtoken)
        if token.dep_ == "nsubjpass" or "nsubj":
            print("nsubjpass or nsubj: ", token.text, token.dep_)
            """
            nominal subject of passive
            """
            objects.append(tokens_to_string(determinate_full_name(token)))
            print("nsubjpass: ", token.text)
            temp_task.object = determinate_full_name(token)

        if token.dep_ == "nsubj":
            # find all nsubj = objects
            # actors.append(token)
            objects.append(tokens_to_string(determinate_full_name(token)))
            temp_task.object = determinate_full_name(token)

    if conditional:
        temp_XOR.tasks.append(temp_task)
        final_tasks.append(temp_XOR)
        print("Return XOR: ", temp_XOR.__str__() + "\n")
    else:
        final_tasks.append(temp_task)
    return final_tasks


def extract_from_sentence(sent_root):
    active = is_active(sent_root)
    if active:
        return extract_from_active_sentence(sent_root)
    elif not active:
        return extract_from_passive_sentence(sent_root)


def determinate_full_name(token):
    """
    :param token: Token that is part of the extended name
    :return: full name as string
    """
    full_name_tokens = [token]
    for subchild in token.children:
        if subchild.dep_ == "amod":
            full_name_tokens.extend(determinate_full_name(subchild))
        if subchild.dep_ == "compound":
            full_name_tokens.extend(determinate_full_name(subchild))

        if subchild.dep_ == "conj":
            full_name_tokens.extend(determinate_full_name(subchild))

        if subchild.dep_ == "cc":
            full_name_tokens.extend(determinate_full_name(subchild))

        if subchild.dep_ == "prep":
            full_name_tokens.extend(determinate_full_name(subchild))

        if subchild.dep_ == "pobj":
            full_name_tokens.extend(determinate_full_name(subchild))

    sorted_tokens = sorted(full_name_tokens, key=lambda token: token.i)
    return sorted_tokens


def determinate_full_verb(token):
    full_name_tokens = []
    if token.pos_ == "VERB":
        full_name_tokens.append(token)
    elif token.pos_ == "AUX":
        full_name_tokens.append(token)
        for subtoken in token.children:
            if subtoken.dep_ == "acomp":
                full_name_tokens.append(subtoken)
                for sub_subtoken in subtoken.children:
                    if sub_subtoken.dep_ == "advmod":
                        full_name_tokens.append(sub_subtoken)
    for subtoken in token.children:
        if subtoken.dep_ == "advmod":
            full_name_tokens.append(subtoken)
    sorted_tokens = sorted(full_name_tokens, key=lambda token: token.i)
    return sorted_tokens


def tokens_to_string(tokens):
    strBuilder = ""
    for token in tokens:
        strBuilder = strBuilder + token.text + " "
    return strBuilder


def check_verb_for_advl(token):
    for sub_token in token.children:
        if sub_token.dep_ == "advcl":  # Verb
            """
            adverbial clause: 
                - provides additional information about the action or verb in the main clause
                - typically answering questions like how, when, where, why, or to what extent
                - can be introduced by subordinating conjunctions such as "although," 
                        "because," "when," "while," "if," "since," "until," and many others
            """
            print("advcl: ", sub_token.text)
            active = is_active(sub_token)
            print("check_verb_for_advl: active: ", active)
            if sub_token.pos_ == "VERB" or "AUX":
                if active:
                    return extract_from_active_sentence(sub_token)
                elif active == False:
                    return extract_from_passive_sentence(sub_token)


def check_verb_for_conditions(token):
    print("check_verb_for_conditions: ", token.text)
    """
    :param token: Root of the sentencen clausel, satarting with the mains sentence
    :return:
    """
    for sub_token in token.children:
        if sub_token.dep_ == "advmod":  # whenever
            print("advmod: ", sub_token.text)
            """
            adverbial modifier: modify or provide additional information about a verb, an adjective, another adverb, or an entire sentence
            """
            condtional_marker.append(sub_token)

        if sub_token.dep_ == "mark":
            """
            marker: used as an abbreviation for the "marker" or "marking" of a grammatical relationship between two parts of a sentence, often involving subordination
            """
            condtional_marker.append(sub_token)
            if sub_token.pos_ == "SCONJ":  # "if," "because," "although," "when," "while," "whether," "since," and "as,"
                pass
            if sub_token.pos_ == "ADV":  # "before" and "after" can also introduce subordinate clauses
                pass
            if sub_token.pos_ == "PART":  # "as" and "so" # "He left, so I stayed."
                pass


actions = []
actors = []
objects = []
helpers = []
condtional_marker = []
tasks = []


def start_process_analysis():
    DecisionElements = []
    Pools = []
    input_path = "/Evaluation/text_input_vh/Text5.txt"
    text_input = open(input_path, 'r').read().replace('\n', ' ')
    doc = nlp(text_input)

    for sent in doc.sents:
        # Filter introduction sentences
        if list(doc.sents).index(sent) == 0 and sent.similarity(doc) < 0.75:
            print("First sentence is not similar enough to the rest of the text: ", sent.similarity(doc))
            continue
        print("*" * 20)

        # Set Additional Attribute "is_active" to True if main clause is active
        sent.set_extension("is_active", default=True, force=True)
        sent._.is_active = is_active1(sent)

        # Set Additional Attribute "is_conditional" to True if sentence is conditional
        sent.set_extension("is_conditional", default=False, force=True)
        sent._.is_conditional = is_condtional(sent)

        # print some details
        print("sent.text :", sent.text)
        print("sent._.is_active: ", sent._.is_active)
        print("sent._.is_conditional: ", sent._.is_conditional)
        print("sent.root.text: ", sent.root.text)

        # start extraction for each sentence
        if sent._.is_active:
            if sent.root.dep_ == "ROOT" and sent.root.pos_ == "VERB":
                tasks.extend(extract_from_active_sentence(sent.root, sent._.is_conditional))

        elif sent._.is_active == False:
            if sent.root.dep_ == "ROOT" and sent.root.pos_ == "VERB" or "AUX":
                tasks.extend(extract_from_passive_sentence(sent.root, sent._.is_conditional))

    print("\n \n")
    print("Output: structure")
    for structure in tasks:
        print("*" * 20)
        if isinstance(structure, XOR):
            print("XOR: ", structure.assign_decision_criteria_to_case())
            # print("XOR: ", structure.assign_decision_criteria_to_case())
        print(structure.__str__())


start_process_analysis()


def determine_end_activities():
    pass


def determine_constuctions(sent):
    pass


def determine_if(sent):
    for token in sent:
        if token.pos_ == "SCONJ":  # IF / whenever
            return True


def determine_else(sent):
    for token in sent:
        if token.pos_ == "SCONJ":  # IF / whenever
            return True
