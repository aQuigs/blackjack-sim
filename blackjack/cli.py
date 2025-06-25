import logging

import click

from blackjack.entities.deck_schema import StandardBlackjackSchema
from blackjack.entities.shoe import Shoe
from blackjack.game import Game, GameResult
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.random import RandomStrategy, StandardDealerStrategy


class BlackjackCLI:
    def __init__(
        self,
        output_tracker=None,
        deck_schema=None,
        rules=None,
        player_strategy=None,
        dealer_strategy=None,
    ):
        self.output_tracker = output_tracker
        self.deck_schema = deck_schema or StandardBlackjackSchema()
        self.rules = rules or StandardBlackjackRules()
        self.player_strategy = player_strategy or RandomStrategy()
        self.dealer_strategy = dealer_strategy or StandardDealerStrategy()

    def run(self, num_players: int, num_decks: int, printable: bool = True) -> GameResult:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        shoe = Shoe(self.deck_schema, num_decks)
        player_strategies = [self.player_strategy for _ in range(num_players)]
        game = Game(
            player_strategies,
            shoe,
            self.rules,
            self.dealer_strategy,
            output_tracker=self.output_tracker,
        )
        result = game.play_round()
        if printable:
            for i, player_result in enumerate(result.player_results):
                hand_str = " ".join(card for card in player_result.hand)
                print(f"Player {i+1} final hand: {hand_str}")
            dealer_hand_str = " ".join(card for card in result.dealer_hand)
            print(f"Dealer final hand: {dealer_hand_str}")
            print(f"Result: {result.winner.name if result.winner else 'Unknown'}")
        return result


@click.command()
@click.option("--num-players", default=1, show_default=True, type=click.IntRange(1, 5), help="Number of players (1-5).")
@click.option("--num-decks", default=1, show_default=True, type=click.IntRange(1, 8), help="Number of decks (1-8).")
@click.option("--no-print", is_flag=True, help="Disable printing of hands and results.")
def main(num_players, num_decks, no_print):
    """Run a blackjack simulation from the command line."""
    try:
        cli = BlackjackCLI()
        cli.run(num_players, num_decks, printable=not no_print)
    except Exception as exc:
        logging.error(f"Error running blackjack simulation: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
