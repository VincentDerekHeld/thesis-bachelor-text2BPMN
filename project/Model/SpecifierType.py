from enum import Enum


class SpecifierType(Enum):
    # The "amod" tag is used to label an adjective that modifies a noun.
    # For example, in the sentence "The red car is fast", the adjective "red" modifies the noun "car"
    AMOD = "amod"
    # The "nn" tag is used to label a noun that is part of a compound noun.
    # For example, in the compound noun "coffee mug", the word "coffee" is labeled as an "nn" because it modifies the noun "mug".
    NN = "nn"
    # prepositional modifier is used to connect a verb, adjective, or noun to a phrase led by a preposition, thereby modifying the original word.
    PREP = "prep"
    # An adjectival complement is an adjective that functions as the complement of a verb, meaning it completes the meaning of the verb.
    # It is often used to describe the subject of the sentence.
    ACOMP = "acomp"
