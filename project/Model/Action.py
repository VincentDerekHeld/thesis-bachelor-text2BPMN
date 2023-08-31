from enum import Enum

from Model.Actor import Actor
from Model.ExtractedObject import ExtractedObject
from Model.Resource import Resource
from spacy.tokens import Token
from typing import Optional

from Utilities import str_utility, string_list_to_string, index_of


class LinkType(Enum):
    TO_PREV = 1
    TO_NEXT = 2

class Action(ExtractedObject):
    def __init__(self, verb):
        super().__init__(verb)
        self.object: Optional[Resource] = None
        self.prepositional_object: Optional[Resource] = None
        self.conjunction: [Action] = []
        self.xcomp: Optional[Action] = None

        # "prt" stands for particle. -> It is a term used in dependency grammar to describe a relationship
        # between a verb and a particle in a phrasal verb.
        # She picked >up< the book.
        # They are looking >into< the problem.
        self.prt: Optional[Token] = None

        # Auxiliary verbs are verbs that are used together with a main verb to provide additional information
        # about the verb's tense, voice, or modality.
        # They >were< playing football.
        # She >had< already left when he arrived.
        self.aux: Optional[Token] = None
        self.advmod = []
        self.dative: Optional[Token] = None

        self.marker: Optional[str] = None
        self.pre_adv_mod: Optional[Token] = None
        self.prep: Optional[Token] = None

        self.negated: bool = False
        self.active: bool = False

        # a specific attribute used for the if condition
        self.subclause = None

        self.link: Optional[Action] = None
        self.link_type: Optional[LinkType] = None

    def __str__(self) -> str:
        result = []
        if self.token is None:
            return ""

        if self.active:
            str_utility(self.token, result)
        else:
            str_utility(self.token.lemma_, result, i=0)

        if self.prt is not None:
            str_utility(self.prt, result)

        if self.token.lemma_ != "be":
            for spec in self.specifiers:
                if spec.SpecifierType.value == "acomp":
                    str_utility(spec.token, result)

        if self.negated:
            index = index_of(self.token, result)
            if index > -1:
                if self.token.lemma_ in ["be", "have"]:
                    result.insert(index + 1, "not")
                else:
                    result.insert(index, "not")

        if self.object is not None:
            if self.prepositional_object is not None:
                if self.object.token != self.prepositional_object.token:
                    str_utility(str(self.object), result, i=self.object.token.i)
            else:
                str_utility(str(self.object), result, i=self.object.token.i)
        elif self.token.lemma_ == "be":
            for child in self.token.children:
                if child.dep_ == "acomp":
                    str_utility(child, result, i=child.i)
                elif child.dep_ == "attr":
                    str_utility(child, result, i=child.i)
                    for det in child.children:
                        if det.dep_ in ["det", "amod", "compound"]:
                            str_utility(det, result, i=det.i)

        if self.prep is not None and self.prepositional_object is not None:
            pobj = str(self.prepositional_object)
            if pobj != "":
                str_utility(self.prep, result)
                str_utility(pobj, result, i=self.prepositional_object.token.i)

        return string_list_to_string(result)
