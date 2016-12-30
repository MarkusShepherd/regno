# -*- coding: utf-8 -*-

"""base cards"""

from __future__ import absolute_import, unicode_literals

import logging

LOGGER = logging.getLogger(__name__)

class Card(object):
    def __init__(self, player, game):
        self.player = player
        self.game = game

    def __str__(self):
        return self.name

    def play(self):
        self.player.in_play.append(self)
        self.player.actions += self.actions
        self.player.buys += self.buys
        for _ in range(self.cards):
            self.player.draw_hand()

    def gain(self):
        self.game.supply[type(self)] -= 1
        self.player.discard_pile.append(type(self))
        LOGGER.info('player %s gained card %s', self.player, self)

    def buy(self):
        self.player.spent_money += self.cost
        LOGGER.info('player %s bought card %s', self.player, self)
        self.gain()

    @property
    def name(self):
        return type(self).__name__

    text = None
    types = frozenset()

    _cost = 0
    @property
    def cost(self):
        return self._cost

    supply = 0

    actions = 0
    buys = 0
    cards = 0
    money = 0
    victory_points = 0

class Copper(Card):
    types = frozenset(['treasure'])
    _cost = 0
    supply = 60
    money = 1

class Silver(Card):
    types = frozenset(['treasure'])
    _cost = 3
    supply = 40
    money = 2

class Gold(Card):
    types = frozenset(['treasure'])
    _cost = 6
    supply = 30
    money = 3

class Estate(Card):
    types = frozenset(['victory'])
    _cost = 2
    supply = 12
    victory_points = 1

class Duchy(Card):
    types = frozenset(['victory'])
    _cost = 5
    supply = 12
    victory_points = 3

class Province(Card):
    types = frozenset(['victory'])
    _cost = 8
    supply = 12
    victory_points = 6

class Curse(Card):
    types = frozenset(['curse'])
    _cost = 0
    supply = 30
    victory_points = -1

BASESET = (Copper, Silver, Gold, Estate, Duchy, Province, Curse)
