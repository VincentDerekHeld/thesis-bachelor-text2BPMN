PERSON_CORRECTOR_LIST = ["resource provisioning", "customer service", "support", "support office", "support officer",
                         "client service back office", "master", "masters", "assembler ag", "acme ag",
                         "acme financial accounting", "secretarial office", "office", "registry", "head", "storehouse",
                         "atm", "crs", "company", "garage", "kitchen", "sommelier", "department", "ec", "sp", "mpo",
                         "mpoo", "mpon", "msp", "mspo", "mspn", "go", "pu", "ip", "inq", "fault detector",
                         "mail processing unit"]

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
