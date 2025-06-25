import logging

import click

from blackjack.entities.deck_schema import StandardBlackjackSchema
from blackjack.entities.shoe import Shoe
from blackjack.game import Game
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.random import RandomStrategy, StandardDealerStrategy


def run_game(num_players: int, num_decks: int, printable: bool = True):
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks)
    rules = StandardBlackjackRules()
    strategy = RandomStrategy()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [strategy for _ in range(num_players)]
    game = Game(player_strategies, shoe, rules, dealer_strategy)
    game.play_round()
    if printable:
        for i, player in enumerate(game.players):
            hand_str = " ".join(str(card) for card in player.hand.cards)
            print(f"Player {i+1} final hand: {hand_str}")
        dealer_hand_str = " ".join(str(card) for card in game.dealer.hand.cards)
        print(f"Dealer final hand: {dealer_hand_str}")
    player_value = rules.hand_value(game.players[0].hand).value
    dealer_value = rules.hand_value(game.dealer.hand).value
    if rules.is_bust(game.players[0].hand):
        result = "Player busts, dealer wins."
    elif rules.is_bust(game.dealer.hand):
        result = "Dealer busts, player wins!"
    elif player_value > dealer_value:
        result = "Player wins!"
    elif player_value < dealer_value:
        result = "Dealer wins."
    else:
        result = "Push (tie)."
    if printable:
        print(f"Result: {result}")


@click.command()
@click.option("--num-players", default=1, show_default=True, type=click.IntRange(1, 5), help="Number of players (1-5).")
@click.option("--num-decks", default=1, show_default=True, type=click.IntRange(1, 8), help="Number of decks (1-8).")
@click.option("--no-print", is_flag=True, help="Disable printing of hands and results.")
def main(num_players, num_decks, no_print):
    """Run a blackjack simulation from the command line."""
    try:
        run_game(num_players, num_decks, printable=not no_print)
    except Exception as exc:
        logging.error(f"Error running blackjack simulation: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
