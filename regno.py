# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import argparse
import json
import logging
import random
import sys

from collections import Counter
from importlib import import_module

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

            LOGGER('Adventurer revealed %s', card.__name__)

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

        candidates = list(self.to_gain)

        if not candidates:
            candidates = [card for card, stack in self.game.supply.items()
                          if stack and card(self.player, self.game).cost <= 4]
            candidates = sorted(candidates, key=lambda card: -card(self.player, self.game).cost)

        for candidate in candidates:
            card = candidate(self.player, self.game)
            if card.cost <= 4 and self.game.supply.get(candidate):
                card.gain()
                return

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

def class_from_path(path):
    parts = path.split('.')

    try:
        if len(parts) == 1:
            return globals().get(path) or import_module(path)

        else:
            obj = import_module(parts[0])
            for part in parts[1:]:
                if not obj:
                    break
                obj = getattr(obj, part, None)
            return obj

    except ImportError:
        return None

def parse_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('strategies', nargs='*',
                        help='strategies')
    parser.add_argument('-g', '--games', type=int, default=10,
                        help='number of games')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='log verbosity (repeat to increase)')

    return parser.parse_args()

def main():
    args = parse_args()

    LOGGER.addHandler(logging.StreamHandler(sys.stdout))
    LOGGER.setLevel(logging.DEBUG if args.verbose >= 2
                    else logging.INFO if args.verbose == 1
                    else logging.WARNING)

    LOGGER.info(args.strategies)

    # strategies = (BigMoney, BigMoneySmithy, BigMoneyMiner, BigMoneyFestival)
    strategies = [class_from_path(strategy) for strategy in args.strategies]
    LOGGER.info(strategies)
    stats = {strategy.__name__: 0 for strategy in strategies}
    summaries = []

    for i in range(args.games):
        LOGGER.info('\n\n#######################################################')
        LOGGER.info('##################### Game #%05d #####################', i + 1)
        LOGGER.info('#######################################################')
        game = Game([Copper, Silver, Gold,
                     Estate, Duchy, Province, Curse,
                     Chancellor, Festival, Gardens, Laboratory,
                     Market, Smithy, Village, Woodcutter,
                     Mine, Witch],
                    [strategy() for strategy in strategies])

        game.play()
        summary = game.stats
        summaries.append(summary)
        for winner in summary['winners']:
            stats[winner] += 1

    print('\n\n\n', json.dumps(summaries, indent=4))
    print(json.dumps(stats, indent=4))

if __name__ == '__main__':
    main()
