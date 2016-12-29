# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging
import random

from collections import Counter

from .cards.base import Copper, Estate, Province

LOGGER = logging.getLogger(__name__)

class Game(object):
    def __init__(self, supply, strategies):
        self.supply = {card: card.supply for card in supply}
        self.players = [Player('Player #{}'.format(i + 1), self, strategy)
                        for i, strategy in enumerate(strategies)]
        random.shuffle(self.players)

        self.current_round = 0
        self.current_player = 0
        self.trash = []

    @property
    def stats(self):
        max_points = max(player.victory_points for player in self.players)
        result = {
            'max_points': max_points,
            'players': [{
                # 'player': player,
                'number': i + 1,
                'strategy': type(player.strategy).__name__,
                'victory_points': player.victory_points,
                'leading': player.victory_points == max_points,
            } for i, player in enumerate(self.players)],
            'current_round': self.current_round + 1,
            'current_player': self.current_player + 1,
        }
        if self.finished():
            result['winners'] = [player['strategy']
                                 for player in result['players']
                                 if player['leading']]

        return result

    def finished(self):
        return self.supply[Province] == 0 or sum(pile == 0 for pile in self.supply.values()) >= 3

    def play(self):
        while not self.finished():
            player = self.players[self.current_player]
            LOGGER.info('\n#######################################################')
            LOGGER.info('play round #%d player #%d (%s)',
                        self.current_round + 1, self.current_player + 1,
                        type(player.strategy).__name__)
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
        LOGGER.info('hand: [%s]', ', '.join(card(player, self).name for card in player.hand))

        player.actions = 1
        player.buys = 1
        player.spent_money = 0

        while player.actions > 0:
            card = player.strategy.action(player, self)
            if card is None:
                LOGGER.info('no more actions to play')
                break

            player.hand.remove(type(card))
            player.actions -= 1
            LOGGER.info('playing action %s', card.name)
            card.play()

        while len(player.hand) > 0:
            card = player.strategy.treasure(player, self)
            if card is None:
                LOGGER.info('no more treasures to play')
                break

            player.hand.remove(type(card))

            LOGGER.info('playing treasure %s', card.name)
            card.play()

        while player.buys > 0:
            card = player.strategy.buy(player, self)
            if card is None:
                LOGGER.info('no more cards to buy')
                break

            player.buys -= 1

            LOGGER.info('buying card %s', card.name)
            card.buy()

        player.discard_pile.extend(player.hand)
        player.discard_pile.extend(type(card) for card in player.in_play)
        player.hand = []
        for _ in range(5):
            player.draw_hand()
        # player.hand = [player.draw() for _ in range(5)]
        player.in_play = []

        player.actions = 1
        player.buys = 1
        player.spent_money = 0

        LOGGER.info('player is done with the turn – next one')

class Player(object):
    def __init__(self, name, game, strategy):
        self.name = name
        self.game = game
        self.strategy = strategy
        self.deck = [Copper] * 7 + [Estate] * 3
        self.discard_pile = []
        random.shuffle(self.deck)

        self.hand = []
        self.in_play = []

        for _ in range(5):
            self.draw_hand()

        self.spent_money = 0

    def __str__(self):
        return self.name

    @property
    def victory_points(self):
        return sum(card.victory_points for card in self.full_deck)
        # return (sum(card(self, self.game).victory_points for card
        #             in self.deck + self.hand + self.discard_pile)
        #         + sum(card.victory_points for card in self.in_play))

    @property
    def money(self):
        return sum(card.money for card in self.in_play) - self.spent_money

    @property
    def cards_total(self):
        return len(self.deck) + len(self.hand) + len(self.in_play) + len(self.discard_pile)

    @property
    def full_deck(self):
        return (tuple(card(self, self.game) for card in self.deck + self.hand + self.discard_pile)
                + tuple(self.in_play))

    @property
    def counter(self):
        return Counter(type(card) for card in self.full_deck)

    def draw(self):
        try:
            return self.deck.pop(0)
        except IndexError:
            LOGGER.info('empty deck – have to shuffle discard pile')
            self.deck = self.discard_pile
            self.discard_pile = []
            random.shuffle(self.deck)
            return self.draw() if len(self.deck) else None

    def draw_hand(self):
        card = self.draw()
        if card:
            LOGGER.info('drew card %s to hand', card.__name__)
            self.hand.append(card)
        else:
            LOGGER.warning('unable to draw card to hand')

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
        buyable = [x for x in game.supply.items()
                   if x[1] > 0 and x[0](player, game).cost <= player.money]
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
