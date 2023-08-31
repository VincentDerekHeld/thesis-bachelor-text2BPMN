from Model.ExtractedObject import ExtractedObject
from spacy.tokens import Token
from Utilities import str_utility, string_list_to_string


class Resource(ExtractedObject):
    def __init__(self, token):
        super().__init__(token)
        self.resolved_token: [Token] = []

    def __str__(self) -> str:
        if self.token is None:
            return ""
        else:
            resource = self.get_all_children()

            if len(self.resolved_token) > 0:
                s = ""
                for r in self.resolved_token:
                    if self.resolved_token.index(r) != len(self.resolved_token) - 1:
                        s += r.text + ", "
                    else:
                        s += r.text

                str_utility(s, resource, self.token.i)
            else:
                str_utility(self.token, resource)

            return string_list_to_string(resource)
