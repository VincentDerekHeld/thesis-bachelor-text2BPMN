from typing import Optional
from spacy.tokens import Span
from Model.Action import Action
from Model.Actor import Actor


class Process:
    def __init__(self, sub_sentence):
        self.sub_sentence: Span = sub_sentence
        self.actor: Optional[Actor] = None
        self.action: Optional[Action] = None

    def __str__(self) -> str:
        return "Sub-sentence: \"" + self.sub_sentence.text + "\""

    def is_invalid(self):
        if self.actor is None and self.action is None:
            return True
        else:
            return False
