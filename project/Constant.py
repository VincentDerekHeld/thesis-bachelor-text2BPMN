DEBUG = False  # Default: False;  True: use small model, False: use large model

LLM_real_actor = True  # Default: True; True: use LLM to decide if real actor based on LLM

LLM_ATR = True  # Default: True; True: activate the LLM-assisted text refinement

LLM_syntax_improval = True  # Default: True; True: activate the LLM-assisted syntax improvement

add_modal_verbs = True  # Default: True; True: Add modal verbs to the input text using the LLM, therefore LLM_ATR must be True

actors_similarity = True  # Default: True; Use the spacy_similarity to determine if two actors are the same, therefore LLM_ATR must be True

resolve_first_lane_problem = True  # Default: True; True: resolve the problem why the first actor is not printed as lane

resolve_syntax_problems = True  # Default: True Resolve syntax problems by filtering keywords from actions

filter_finish_activities = True  # Default: True; Filter finish activities from the list of structure and determine new end activities
less_end_gateways = False  # Default: True; True: Use less end gateways
less_end_gateways2 = True

filter_irrelevant_information = True  # Default: True; Filter irrelevant information from the input text using the LLM, therefore LLM_ATR must be True
transform_implicit_actions = True  # Default: True; Transform implicit actions into explicit actions using the LLM, therefore LLM_ATR must be True
resolve_enumeration = True  # Default: True; Resolve enumerations using the LLM, therefore LLM_ATR must be True

filter_example_sentences_regex = False  # Default: False; Filter example sentences from the input text using the regular expression
remove_introduction_sentence_with_spacy = False  # Default: False; Remove introduction sentences from the input text using the spacy_similarity

NOT_END_ACTIVITY_VERBS = ["withdraws consent", "objects to the processing", "base the processing"]

MODAL_VERBS = ["can", "could", "may", "might", "must", "shall", "should", "will", "would"]

PERSON_CORRECTOR_LIST = ["resource provisioning", "customer service", "support", "support office", "support officer",
                         "client service back office", "master", "masters", "assembler ag", "acme ag",
                         "acme financial accounting", "secretarial office", "office", "registry", "head", "storehouse",
                         "atm", "crs", "company", "garage", "kitchen", "sommelier", "department", "ec", "sp", "mpo",
                         "mpoo", "mpon", "msp", "mspo", "mspn", "go", "pu", "ip", "inq", "fault detector",
                         "mail processing unit", "data subject", "data subjects", "data controller", "terminal",
                         "switching device", "meter", "control panel"]

REAL_ACTOR_DETERMINERS = ["person", "social_group", "software system"]

META_ACTOR_DETERMINERS = ["step", "process", "case", "state"]

SUBJECT_PRONOUNS = ["I", "you", "he", "she", "it", "we", "you", "they"]
OBJECT_PRONOUNS = ["me", "you", "him", "her", "it", "us", "you", "them"]
POSSESSIVE_ADJECTIVES = ["my", "your", "his", "her", "its", "our", "your", "their"]
POSSESSIVE_PRONOUNS = ["mine", "yours", "his", "hers", "ours", "yours", "theirs"]

#  "whereas", "optionally"
SINGLE_IF_CONDITIONAL_INDICATORS = ["if", "whether"]

SINGLE_ELSE_CONDITIONAL_INDICATORS = ["else", "otherwise"]

# COMPOUND_CONDITIONAL_INDICATORS = ["in case of", "in the case of", "in case", "for the case"]
COMPOUND_CONDITIONAL_INDICATORS = [
    {"in/for (the) case (of)": [
        {"LEMMA": {"IN": ["in", "for"]}},
        {"LEMMA": "the", "OP": "?"},
        {"LEMMA": "case"},
        {"POS": "ADP", "OP": "?"},
    ]}
]

SINGLE_PARALLEL_INDICATORS = ["while", "meanwhile", "concurrently", "meantime"]

# COMPOUND_PARALLEL_INDICATORS = ["in parallel", "in the meantime"]
COMPOUND_PARALLEL_INDICATORS = [
    {"in parallel": [
        {"LEMMA": "in"},
        {"LEMMA": "parallel"},
    ]},
    {"in (the) meantime": [
        {"LEMMA": "in"},
        {"POS": "DET", "OP": "?"},
        {"LEMMA": "meantime"}
    ]}
]

SINGLE_SEQUENCE_INDICATORS = ["then", "after", "afterward", "afterwards", "subsequently", "thus"]

# COMPOUND_SEQUENCE_INDICATORS = ["based on this"]
COMPOUND_SEQUENCE_INDICATORS = [
    {"based (on/of)": [
        {"LEMMA": "base"},
        {"POS": "ADP"},
    ]}
]

EXCEPTION_INDICATORS = ["except"]

STRING_EXCLUSION_LIST = []

CASE_INDICATORS = [
    {"in/for (the) former/latter case (of)": [
        {"LEMMA": {"IN": ["in", "for"]}},
        {"LEMMA": "the", "OP": "?"},
        {"LEMMA": {"IN": ["former", "latter"]}},
        {"LEMMA": "case"},
        {"POS": "ADP", "OP": "?"},
    ]}
]
