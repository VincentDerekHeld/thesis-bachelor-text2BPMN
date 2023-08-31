from typing import Optional
import WordNetWrapper
from Model.Action import Action
from Model.Actor import Actor
from Model.Resource import Resource
from Model.SentenceContainer import SentenceContainer
from Model.Specifier import Specifier
from Model.SpecifierType import SpecifierType
from Utilities import find_dependency, anaphora_resolver, belongs_to_other_process, find_process, \
    get_complete_actor_name

from spacy.tokens import Token


def create_actor(main_actor: Token) -> Optional[Actor]:
    """
    Creates an actor from a token, resolves the reference and then determines the noun specifiers for the actor.

    Args:
        main_actor: the token for the actor

    Returns:
        the created actor object
    """
    if main_actor is None:
        return None

    actor = Actor(main_actor)
    anaphora_resolver(actor)
    determine_noun_specifiers(actor)
    if len(actor.resolved_token) > 0:
        complete_name = get_complete_actor_name(actor.resolved_token[0])
    else:
        complete_name = get_complete_actor_name(main_actor)
    actor.full_name = complete_name.strip()

    if not WordNetWrapper.can_be_person_or_system(complete_name, main_actor):
        actor.is_real_actor = False
    return actor


def create_object(obj: Token) -> Optional[Resource]:
    """
    Creates a resource from a token, resolves the reference and then determines the noun specifiers for the resource.
    Args:
        obj: the token for the resource

    Returns: the created resource object

    """
    if obj is None:
        return None

    resource = Resource(obj)
    anaphora_resolver(resource)
    determine_noun_specifiers(resource)
    return resource


def create_action(verb: Token, noun: Token) -> Optional[Action]:
    """
    Creates an action from a verb and a noun token. It also determines the verb specifiers for the action.

    Args:
        verb: the verb token for the action
        noun: the noun token for the object

    Returns: the created action object

    """
    if verb is None:
        return None

    action = Action(verb)

    if noun is not None:
        resource = create_object(noun)
        action.object = resource

    aux = find_dependency(["aux"], token=verb)
    action.aux = aux[0] if len(aux) > 0 else None

    modifiers = find_dependency(["advmod"], token=verb)
    action.advmod.extend(modifiers)

    negate = is_negated(verb, noun)
    action.negated = negate

    prt = find_dependency(["prt"], token=verb)
    action.prt = prt[0] if len(prt) > 0 else None

    pobj = find_pobj(verb)
    action.prepositional_object = Resource(pobj) if pobj is not None else None

    dative = find_dependency(["dative"], token=verb)
    action.dative = dative[0] if len(dative) > 0 else None

    find_verb_specifiers(action)
    return action


def find_pobj(verb: Token):
    """
    Finds the prepositional object of a verb token.
    Args:
        verb: the verb token

    Returns:
        if the prepositional object token is found, it is returned, otherwise None is returned
    """
    pobj = find_dependency(["pobj"], token=verb)
    if len(pobj) == 0:
        prep = find_dependency(["prep"], token=verb)
        for p in prep:
            if p.text in ["for", "to", "into", "of"]:
                pobj = find_dependency(["pobj"], token=p)

    if len(pobj) > 0:
        return pobj[0]
    else:
        return None


def determine_noun_specifiers(actor):
    """
    Determines the noun specifiers for an actor token.
    Args:
        actor: the actor token
    """
    find_determiner(actor)
    find_compound(actor)
    find_amod_specifiers(actor)
    find_nn_specifier(actor)


def find_verb_specifiers(action):
    """
    Determines the verb specifiers for an action token.
    Args:
        action: the action token

    """
    find_prep_specifier(action)
    find_acomp_specifier(action)


def find_determiner(actor):
    """
    Finds the determiner (the, a, any, some etc.) of an actor token.
    Args:
        actor: the actor token
    """
    determiner_list = find_dependency(["det", "poss"], token=actor.token)
    if len(determiner_list) > 0:
        actor.determiner = determiner_list[0]


def find_compound(actor):
    """
    Finds the compound noun of an actor token.
    Args:
        actor: the actor token
    """
    compound_list = find_dependency(["compound"], token=actor.token, deep=True)
    actor.add_compound(compound_list)


def find_amod_specifiers(actor):
    """
    Finds the adjective modifiers of an actor token.
    The "amod" tag is used to label an adjective that modifies a noun.
    For example, in the sentence "The red car is fast", the adjective "red" modifies the noun "car"
    Args:
        actor: the actor token

    """

    amod_specifiers = find_dependency(["amod"], token=actor.token)
    for a in amod_specifiers:
        specifier = Specifier(a, SpecifierType.AMOD, a.text)
        actor.add_modifier(specifier)


def find_nn_specifier(actor):
    """
    Finds the noun-noun modifiers of an actor token.
    The "nn" tag is used to label a noun that is part of a compound noun.
    For example, in the compound noun "coffee mug", the word "coffee" is labeled as an "nn" because it modifies the noun "mug".
    Args:
        actor: the actor token
    """

    nn_specifiers = find_dependency(["nn"], token=actor.token)
    for s in nn_specifiers:
        specifier = Specifier(s, SpecifierType.NN, s.text)
        actor.add_modifier(specifier)


def find_prep_specifier(action):
    """
    Finds the prepositional modifiers of an action token.
    Args:
        action: the action token
    """
    prep_specifiers = find_dependency(["prep"], token=action.token)
    for p in prep_specifiers:
        specifier = Specifier(p, SpecifierType.PREP, p.text)
        action.add_modifier(specifier)


def find_acomp_specifier(action):
    """
    Finds the adjectival complement modifiers of an action token.
    Args:
        action: the action token

    """
    acomp_specifiers = find_dependency(["acomp"], token=action.token)
    for a in acomp_specifiers:
        specifier = Specifier(a, SpecifierType.ACOMP, a.text)
        action.add_modifier(specifier)


def is_negated(verb: Token, noun: Token) -> bool:
    """
    Determines if a verb is negated.
    Args:
        verb: the verb token
        noun: the noun token

    Returns:
        True if the verb is negated, otherwise False
    """
    negation_list = ["no", "not", "n't"]
    for child in verb.children:
        if child.dep_ == "neg":
            return True

    if noun is not None:
        for child in noun.children:
            if child.dep_ == "det" and child.text in negation_list:
                return True

    return False


def correct_model(container: SentenceContainer):
    """
    Corrects the model. The women who lives next door is a doctor -> (The women) (who lives next door) (is a doctor)
    -> (The women is a doctor) (who lives next door)
    Args:
        container: the container with the sentence

    """
    for process in container.processes:
        if process.is_invalid():
            insertion_index = belongs_to_other_process(process.sub_sentence.root, container)
            if insertion_index is None:
                container.remove_process(sub_sentence=process.sub_sentence)
                continue
            deletion_index = container.processes.index(find_process(container, sub_sent=process.sub_sentence))
            # swap the insertion_index and deletion_index
            container.processes[insertion_index], container.processes[deletion_index] = container.processes[
                deletion_index], container.processes[insertion_index]
            container.remove_process(sub_sentence=process.sub_sentence)
