from Model.ExtractedObject import ExtractedObject
from spacy.tokens import Token
from Utilities import str_utility, string_list_to_string


class Actor(ExtractedObject):
    def __init__(self, token):
        super().__init__(token)
        self.full_name: str = ""
        self.resolved_token: [Token] = []
        # A “real”-Actor, as a person, an organization or a software system. -> [“person”, “social group”, “software system”]
        self.is_real_actor = True
        self.is_meta_actor = False

    def __str__(self) -> str:
        if self.token is None:
            return ""
        else:
            actor = self.get_all_children()

        if len(self.resolved_token) > 0:
            s = ""
            for a in self.resolved_token:
                if self.resolved_token.index(a) != len(self.resolved_token) - 1:
                    s += a.text + ", "
                else:
                    s += a.text

            str_utility(s, actor, self.token.i)
        else:
            str_utility(self.token, actor)

        return string_list_to_string(actor)
