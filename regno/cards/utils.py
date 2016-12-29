# -*- coding: utf-8 -*-

from __future__ import absolute_import

import random

from .base import Card, BASESET

def card_classes(module):
    for obj in dir(module):
        cls = getattr(module, obj)
        try:
            if issubclass(cls, Card):
                yield cls
        except TypeError:
            pass

def random_set(module, num=10, base=BASESET):
    cards = list(card_classes(module))
    random.shuffle(cards)
    return cards[:num] + base if base else cards[:num]
