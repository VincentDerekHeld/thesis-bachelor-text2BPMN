from typing import Optional
from spacy.tokens import Token
from Model.Specifier import Specifier
from Model.SpecifierType import SpecifierType
from Utilities import str_utility


class ExtractedObject:

    def __init__(self, token):
        self.token: Token = token
        # Some examples of determiners in English include "a", "an", "the", "this", "that", "these", "those",
        # "my", "your", "his", "her", "its", "our", and "their".
        self.determiner: Optional[Token] = None
        self.compound: [Token] = []

        self.specifiers: [Specifier] = []

    def add_compound(self, compound):
        self.compound.extend(compound)

    def add_modifier(self, modifier):
        self.specifiers.append(modifier)

    def get_specifiers(self, specifier_type: [SpecifierType] = None) -> [Specifier]:
        if specifier_type is None:
            return self.specifiers
        else:
            result = []
            for m in self.specifiers:
                if m.SpecifierType.value in specifier_type:
                    result.append(m)
            return result

    def get_all_children(self):
        result = []
        self.help_get_all_children(self.token, result)
        return result

    def help_get_all_children(self, token, result):
        for child in token.children:
            if child.dep_ in ["relcl", "punct", "acl"]:
                continue
            self.help_get_all_children(child, result)
            str_utility(child, result)
        return result
