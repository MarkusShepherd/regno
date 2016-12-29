# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import logging
import random

from .core import Strategy
from .cards.base import Copper, Curse, Silver, Gold, Estate, Duchy, Province
from .cards.original import Festival, Gardens, Market, Mine, Smithy, Witch, Woodcutter

LOGGER = logging.getLogger(__name__)

class Smarter(Strategy):
    def action(self, player, game):
        LOGGER.info('player has %d action(s)', player.actions)
        playable = [card for card in player.hand if 'action' in card.types]
        random.shuffle(playable)
        playable = sorted(playable, key=lambda x: -x(player, game).buys)
        playable = sorted(playable, key=lambda x: -x(player, game).cards)
        playable = sorted(playable, key=lambda x: -x(player, game).money)
        playable = sorted(playable, key=lambda x: -x(player, game).actions)
        return playable[0](player, game) if playable else None

    def buy(self, player, game):
        candidate = super().buy(player, game)
        if (isinstance(candidate, Copper)
                or (isinstance(candidate, Estate) and game.supply[Province] > 4)):
            return None
        else:
            return candidate

class BigMoney(Strategy):
    interesting_cards = frozenset((Province, Duchy, Estate, Gold, Silver))

    def buy(self, player, game):
        LOGGER.info('player has %d buy(s) and %d money', player.buys, player.money)
        buyable = [x for x in game.supply.items()
                   if (x[1] > 0 and x[0](player, game).cost <= player.money
                       and x[0] in self.interesting_cards)]
        buyable = sorted(buyable, key=lambda x: -x[0](player, game).cost)
        return buyable[0][0](player, game) if buyable else None

class BigMoneySmithy(BigMoney, Smarter):
    def buy(self, player, game):
        LOGGER.info('player has %d buy(s) and %d money', player.buys, player.money)

        if 4 <= player.money <= 5 and game.supply.get(Smithy) and player.counter[Smithy] < 3:
            return Smithy(player, game)

        return super().buy(player, game)

class BigMoneyFestival(BigMoneySmithy):
    def buy(self, player, game):
        LOGGER.info('player has %d buy(s) and %d money', player.buys, player.money)

        if player.money == 5 and game.supply.get(Festival) and player.counter[Festival] < 2:
            return Festival(player, game)

        return super().buy(player, game)

class BigMoneyMiner(BigMoney):
    def action(self, player, game):
        LOGGER.info('player has %d action(s)', player.actions)

        if Mine in player.hand and (Copper in player.hand or Silver in player.hand):
            if Silver in player.hand:
                return Mine(player, game, Silver)
            else:
                return Mine(player, game, Copper)

        return super().action(player, game)

    def buy(self, player, game):
        LOGGER.info('player has %d buy(s) and %d money', player.buys, player.money)

        if 5 <= player.money <= 7 and game.supply.get(Mine) and player.counter[Mine] < 3:
            return Mine(player, game)

        return super().buy(player, game)

class BigMoneyWitch(BigMoney, Smarter):
    def buy(self, player, game):
        LOGGER.info('player has %d buy(s) and %d money', player.buys, player.money)

        if player.money == 5 and game.supply.get(Witch) and player.counter[Witch] < 3:
            return Witch(player, game)

        return super().buy(player, game)

class Gardener(Smarter):
    def buy(self, player, game):
        LOGGER.info('player has %d buy(s) and %d money', player.buys, player.money)

        if player.money == 5 and game.supply.get(Festival) and player.counter[Festival] < 5:
            return Festival(player, game)
        if player.money == 5 and not game.supply.get(Festival) \
                and game.supply.get(Market) \
                and player.counter[Festival] + player.counter[Market] < 5:
            return Market(player, game)
        if 4 <= player.money <= 5 and game.supply.get(Gardens):
            return Gardens(player, game)
        if player.money == 3 and game.supply.get(Woodcutter):
            return Woodcutter(player, game)

        candidate = super().buy(player, game)

        if (candidate is None or isinstance(candidate, Curse)) and game.supply.get(Copper):
            return Copper(player, game)
        else:
            return candidate
