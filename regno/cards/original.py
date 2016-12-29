# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, unicode_literals

import logging

from .base import Card, Copper, Curse

LOGGER = logging.getLogger(__name__)

class Adventurer(Card):
    types = frozenset(['action'])
    _cost = 6
    supply = 10

    def play(self):
        super().play()

        treasures = []
        others = []

        while len(treasures) < 2:
            card = self.player.draw()

            if card is None:
                LOGGER.warning('deck and discard pile are empty, no more cards to draw')
                break

            LOGGER.info('Adventurer revealed %s', card.__name__)

            if 'treasure' in card.types:
                treasures.append(card)
            else:
                others.append(card)

        self.player.hand.extend(treasures)
        self.player.discard_pile.extend(treasures)

class Chancellor(Card):
    def __init__(self, player, game, discard_deck=True):
        super().__init__(player, game)
        self.discard_deck = discard_deck

    types = frozenset(['action'])
    _cost = 3
    supply = 10
    money = 2

    def play(self):
        super().play()

        if self.discard_deck:
            self.player.discard_pile.extend(self.player.deck)
            self.player.deck = []

class CouncilRoom(Card):
    types = frozenset(['action'])
    _cost = 5
    supply = 10
    buys = 1
    cards = 4

    def play(self):
        for player in self.game.players:
            if player is not self.player:
                player.draw_hand()

class Festival(Card):
    types = frozenset(['action'])
    _cost = 5
    supply = 10
    actions = 2
    buys = 1
    money = 2

class Gardens(Card):
    types = frozenset(['victory'])
    _cost = 4
    supply = 12

    @property
    def victory_points(self):
        return self.player.cards_total // 10

class Laboratory(Card):
    types = frozenset(['action'])
    _cost = 5
    supply = 10
    actions = 1
    cards = 2

class Market(Card):
    types = frozenset(['action'])
    _cost = 5
    supply = 10
    actions = 1
    buys = 1
    cards = 1
    money = 1

class Mine(Card):
    def __init__(self, player, game, to_trash=None, to_gain=None):
        super().__init__(player, game)
        self.to_trash = to_trash
        self.to_gain = to_gain
        if isinstance(self.to_gain, type):
            self.to_gain = {self.to_gain}

    types = frozenset(['action'])
    _cost = 5
    supply = 10

    def play(self):
        super().play()

        if not self.to_trash:
            # TODO test if no treasure in hand
            return

        self.player.hand.remove(self.to_trash)
        self.game.trash.append(self.to_trash)

        LOGGER.info('trashed %s', self.to_trash.__name__)

        money = self.to_trash(self.player, self.game).cost + 3

        gainable = [x[0] for x in self.game.supply.items()
                    if x[1] > 0 and 'treasure' in x[0].types
                    and x[0](self.player, self.game).cost <= money]

        if self.to_gain:
            gainable = [card for card in gainable if card in self.to_gain]

        gainable = sorted(gainable, key=lambda x: -x(self.player, self.game).cost)

        if gainable:
            gainable[0](self.player, self.game).gain()
            gained = self.player.discard_pile.pop()
            self.player.hand.append(gained)
            LOGGER.info('gained %s', gained.__name__)

class Moneylender(Card):
    types = frozenset(['action'])
    _cost = 4
    supply = 10

    def play(self):
        try:
            self.player.hand.remove(Copper)
        except ValueError:
            LOGGER.info('no Copper to trash')
            return

        self.game.trash.append(Copper)
        self.money = 3
        super().play()

class Remodel(Card):
    def __init__(self, player, game, to_trash=None, to_gain=None):
        super().__init__(player, game)
        self.to_trash = to_trash
        self.to_gain = to_gain
        if isinstance(self.to_gain, type):
            self.to_gain = [self.to_gain]

    types = frozenset(['action'])
    _cost = 4
    supply = 10

    def play(self):
        super().play()

        if not self.to_trash:
            # TODO choose randomly
            return

        self.player.hand.remove(self.to_trash)
        self.game.trash.append(self.to_trash)
        money = self.to_trash(self.player, self.game).cost + 2

        candidates = list(self.to_gain)

        if not candidates:
            candidates = [card for card, stack in self.game.supply.items()
                          if stack and card(self.player, self.game).cost <= money]
            candidates = sorted(candidates, key=lambda card: -card(self.player, self.game).cost)

        for candidate in candidates:
            card = candidate(self.player, self.game)
            if card.cost <= money and self.game.supply.get(candidate):
                card.gain()
                return

class Smithy(Card):
    types = frozenset(['action'])
    _cost = 4
    supply = 10
    cards = 3

class Village(Card):
    types = frozenset(['action'])
    _cost = 3
    supply = 10
    actions = 2
    cards = 1

class Witch(Card):
    types = frozenset(['action', 'attack'])
    _cost = 5
    supply = 10
    cards = 2

    def play(self):
        super().play()

        for player in self.game.players:
            if not self.game.supply.get(Curse):
                break

            if player is self.player:
                continue

            Curse(player, self.game).gain()

class Woodcutter(Card):
    types = frozenset(['action'])
    _cost = 3
    supply = 10
    buys = 1
    money = 2

class Workshop(Card):
    def __init__(self, player, game, to_gain=None):
        super().__init__(player, game)
        self.to_gain = to_gain
        if isinstance(self.to_gain, type):
            self.to_gain = [self.to_gain]

    types = frozenset(['action'])
    _cost = 3
    supply = 10

    def play(self):
        super().play()

        candidates = list(self.to_gain) if self.to_gain else ()

        if not candidates:
            candidates = [card for card, stack in self.game.supply.items()
                          if stack and card(self.player, self.game).cost <= 4]
            candidates = sorted(candidates, key=lambda card: -card(self.player, self.game).cost)

        for candidate in candidates:
            card = candidate(self.player, self.game)
            if card.cost <= 4 and self.game.supply.get(candidate):
                card.gain()
                return
