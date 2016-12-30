# -*- coding: utf-8 -*-

"""runs a simulation with the given strategies"""

from __future__ import absolute_import, unicode_literals

import argparse
import json
import logging
import sys

from .cards import random_set
from .core import Game
from .utils import class_from_path

LOGGER = logging.getLogger(__name__)

def parse_args():
    """parse command line arguments"""

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('strategies', nargs=4,
                        help='strategies')
    parser.add_argument('-c', '--card', nargs='*', default=(),
                        help='card(s) to include in the set')
    parser.add_argument('-s', '--set', default='regno.cards.original',
                        help='card collection')
    parser.add_argument('-g', '--games', type=int, default=10,
                        help='number of games')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='log verbosity (repeat to increase)')

    return parser.parse_args()

def main():
    """main function"""

    args = parse_args()

    logging.basicConfig(stream=sys.stdout,
                        level=logging.WARNING - 10 * args.verbose)

    strategies = []
    for strategy in args.strategies:
        cls = class_from_path(strategy)
        if cls is None:
            LOGGER.warning('unable to import strategy %s', strategy)
        else:
            strategies.append(cls)

    LOGGER.info('loaded strategies [%s]', ', '.join(strategy.__name__ for strategy in strategies))

    if len(strategies) != 4:
        raise ValueError('specify 4 strategies (repeat if necessary)')

    stats = {strategy.__name__: 0 for strategy in strategies}
    summaries = []

    module = class_from_path(args.set)
    LOGGER.info('choosing sets from %s', module.__name__)

    args_cards = list(filter(None, map(class_from_path, args.card)))
    LOGGER.info('fixed cards for every set: [%s]',
                ', '.join(sorted(card.__name__ for card in args_cards)))

    for i in range(args.games):
        LOGGER.info('#######################################################')
        LOGGER.info('##################### Game #%05d #####################', i + 1)
        LOGGER.info('#######################################################')
        cards = random_set(module, cards=args_cards)
        LOGGER.info('supply: [%s]', ', '.join(sorted(card.__name__ for card in cards)))
        game = Game(cards, [strategy() for strategy in strategies])

        game.play()
        summary = game.stats
        summaries.append(summary)
        for winner in summary['winners']:
            stats[winner] += 1

    print(json.dumps(summaries, indent=4))
    print(json.dumps(stats, indent=4))

if __name__ == '__main__':
    main()
