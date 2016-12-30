# -*- coding: utf-8 -*-

"""card utility functions"""

from __future__ import absolute_import

import random

from .base import Card, BASESET

def card_classes(module):
    """finds all cards in the given module"""

    for obj in dir(module):
        cls = getattr(module, obj)
        try:
            if issubclass(cls, Card) and cls is not Card:
                yield cls
        except TypeError:
            pass

def random_set(module=None, cards=None, num=10, base=BASESET):
    """creates a set of num cards from the module, with the given cards included, and base added"""

    cards = list(cards) if cards else []
    remaining = num - len(cards)

    if remaining > 0 and module:
        avail_cards = list(card_classes(module))
        if cards:
            avail_cards = [card for card in avail_cards if card not in cards]
        random.shuffle(avail_cards)

        cards += avail_cards[:remaining]

    return cards + list(base) if base else cards
