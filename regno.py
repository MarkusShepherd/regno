# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import random
import sys

LOGGER = logging.getLogger(__name__)

class Game(object):
    def __init__(self, supply, strategies):
        self.supply = {card: card.supply for card in supply}
        self.players = [Player(self, strategy) for strategy in strategies]
        random.shuffle(self.players)

        self.current_round = 0
        self.current_player = 0
        self.trash = []

    def finished(self):
        return (self.supply[Province] == 0 or sum(pile == 0 for pile in self.supply.values()) >= 3)

    def play(self):
        while not self.finished():
            LOGGER.info('\n#######################################################')
            LOGGER.info('play round #%d player #%d', self.current_round, self.current_player + 1)
            player = self.players[self.current_player]
            self.play_round(player)
            self.current_player += 1

            if self.current_player >= len(self.players):
                self.current_player = 0
                self.current_round += 1

            # LOGGER.info(self.supply)

        max_points = max(player.victory_points for player in self.players)
        for i, player in enumerate(self.players):
            LOGGER.info('#%d Player: %d victory points with strategy %s',
                        i + 1, player.victory_points, type(player.strategy).__name__)
            if player.victory_points == max_points:
                LOGGER.info('Player #%d has won!', i + 1)

    def play_round(self, player):
        player.actions = 1
        player.buys = 1
        player.spent_money = 0

        while player.actions > 0:
            card = player.strategy.action(player, game)
            if card is None:
                LOGGER.info('no more actions to play')
                break

            player.hand.remove(type(card))
            player.actions -= 1
            LOGGER.info('playing action %s', card.name)
            card.play()

        while len(player.hand) > 0:
            card = player.strategy.treasure(player, game)
            if card is None:
                LOGGER.info('no more treasures to play')
                break

            player.hand.remove(type(card))

            LOGGER.info('playing treasure %s', card.name)
            card.play()

        while player.buys > 0:
            card = player.strategy.buy(player, game)
            if card is None:
                LOGGER.info('no more cards to buy')
                break

            player.buys -= 1

            LOGGER.info('buying card %s', card.name)
            card.buy()

        player.discard_pile.extend(player.hand)
        player.discard_pile.extend(type(card) for card in player.in_play)
        player.hand = [player.draw() for _ in range(5)]
        player.in_play = []

        player.actions = 1
        player.buys = 1
        player.spent_money = 0

        LOGGER.info('player is done with the turn – next one')

class Player(object):
    def __init__(self, game, strategy):
        self.game = game
        self.strategy = strategy
        self.deck = [Copper] * 7 + [Estate] * 3
        self.discard_pile = []
        random.shuffle(self.deck)

        self.hand = [self.draw() for _ in range(5)]
        self.in_play = []

        self.spent_money = 0

    @property
    def victory_points(self):
        return (sum(card(self, self.game).victory_points for card
                    in self.deck + self.hand + self.discard_pile)
                + sum(card.victory_points for card in self.in_play))

    @property
    def money(self):
        return sum(card.money for card in self.in_play) - self.spent_money

    @property
    def cards_total(self):
        return len(self.deck) + len(self.hand) + len(self.in_play) + len(self.discard_pile)

    def draw(self):
        try:
            return self.deck.pop(0)
        except IndexError:
            self.deck = self.discard_pile
            self.discard_pile = []
            random.shuffle(self.deck)
            return self.deck.pop(0)

class Strategy(object):
    def action(self, player, game):
        LOGGER.info('player has %d action(s)', player.actions)
        playable = [card for card in player.hand if 'action' in card.types]
        return random.choice(playable)(player, game) if playable else None

    def treasure(self, player, game):
        for card in player.hand:
            if 'treasure' in card.types:
                return card(player, game)

    def buy(self, player, game):
        LOGGER.info('player has %d buy(s) and %d money', player.buys, player.money)
        buyable = [x for x in game.supply.items() if x[1] > 0 and x[0](player, game).cost <= player.money]
        random.shuffle(buyable)
        # LOGGER.info(buyable)
        buyable = sorted(buyable, key=lambda x: -x[0](player, game).cost)
        # LOGGER.info(buyable)
        return buyable[0][0](player, game) if buyable else None

    def reaction(self, player, game):
        reactions = [card for card in player.hand if 'reaction' in card.types]
        random.shuffle(reactions)
        for reaction in reactions:
            yield reaction(player, game)

class Card(object):
    def __init__(self, player, game):
        self.player = player
        self.game = game

    def play(self):
        self.player.in_play.append(self)
        self.player.actions += self.actions
        self.player.buys += self.buys
        self.player.hand.extend(self.player.draw() for _ in range(self.cards))

    def buy(self):
        self.player.spent_money += self.cost
        self.game.supply[type(self)] -= 1
        self.player.discard_pile.append(type(self))

    @property
    def name(self): return type(self).__name__
    text = None
    types = frozenset()

    _cost = 0
    @property
    def cost(self): return self._cost

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

class Chancellor(Card):
    types = frozenset(['action'])
    _cost = 3
    supply = 10
    money = 2

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

class Woodcutter(Card):
    types = frozenset(['action'])
    _cost = 3
    supply = 10
    buys = 1
    money = 2

if __name__ == '__main__':
    LOGGER.addHandler(logging.StreamHandler(sys.stdout))
    LOGGER.setLevel(logging.INFO)

    game = Game([Copper, Silver, Gold, Estate, Duchy, Province,
                 Chancellor, Festival, Gardens, Laboratory,
                 Market, Smithy, Village, Woodcutter], [Strategy()] * 4)
    game.play()
