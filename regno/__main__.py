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
    parser.add_argument('strategies', nargs='+',
                        help='strategies')
    parser.add_argument('-s', '--set', default='regno.cards.original',
                        help='number of games')
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

    LOGGER.info(args.strategies)

    strategies = []
    for strategy in args.strategies:
        cls = class_from_path(strategy)
        if cls is None:
            raise ValueError('unable to import strategy {}'.format(strategy))
        strategies.append(cls)

    LOGGER.info(strategies)
    stats = {strategy.__name__: 0 for strategy in strategies}
    summaries = []

    module = class_from_path(args.set)
    LOGGER.info(module)

    for i in range(args.games):
        LOGGER.info('#######################################################')
        LOGGER.info('##################### Game #%05d #####################', i + 1)
        LOGGER.info('#######################################################')
        cards = random_set(module)
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
