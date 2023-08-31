from typing import Optional


class Structure:
    ID_COUNTER = 0

    def __init__(self):
        Structure.ID_COUNTER += 1
        self.id = Structure.ID_COUNTER
        self.is_end_activity = False

        self.previous: Optional[Structure] = None
        self.next: Optional[Structure] = None


class LinkedStructure:
    def __init__(self):
        self.head: Optional[Structure] = None
        self.tail: Optional[Structure] = None

    def add_structure(self, structure):
        if self.head is None:
            self.head = structure
            self.tail = structure
        else:
            self.tail.next = structure
            structure.previous = self.tail
            self.tail = structure

    def __str__(self):
        string = ""
        structure = self.head
        while structure is not None:
            string += str(structure) + "\n"
            structure = structure.next
        return string
