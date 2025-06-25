from blackjack.cli import BlackjackCLI
from blackjack.strategy.base import Strategy
from blackjack.strategy.random import StandardDealerStrategy
from blackjack.game import PlayerOutcome, Winner
from blackjack.entities.card import Card


class AlwaysHitStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "HIT"), available_actions[0])


class AlwaysStandStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "STAND"), available_actions[0])


def test_game_all_players_bust():
    # Player 1: 10, 9, 5 = 24 (bust)
    # Player 2: 10, 8, 6 = 24 (bust)
    # Dealer: 2, 2
    shoe_cards = [
        Card("10", "♠"), Card("10", "♥"), Card("2", "♣"),
        Card("9", "♦"),  Card("8", "♠"), Card("2", "♦"),
        Card("5", "♣"),  Card("6", "♥"),
    ]
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )
    result = cli.run(num_players=2, printable=False)
    for player_result in result.player_results:
        assert player_result.outcome == PlayerOutcome.BUST


def test_game_all_players_blackjack():
    # P1: A♠, K♠ (blackjack)
    # P2: A♥, K♥ (blackjack)
    # D: 9♣, 8♣
    shoe_cards = [
        Card("A", "♠"), Card("A", "♥"), Card("9", "♣"),
        Card("K", "♠"), Card("K", "♥"), Card("8", "♣"),
    ]
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )
    result = cli.run(num_players=2, printable=False)
    for player_result in result.player_results:
        assert player_result.outcome == PlayerOutcome.BLACKJACK


def test_player_wins_when_dealer_busts():
    # P1: 10♠, Q♠ (20, stands)
    # D: 9♠, 5♣ (14), hits 8♣ (22, bust)
    shoe_cards = [
        Card("10", "♠"), Card("9", "♠"), Card("Q", "♠"),
        Card("5", "♣"), Card("8", "♣"),
    ]
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )
    result = cli.run(num_players=1, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.ACTIVE
    assert result.winner == Winner.PLAYER


def test_game_push():
    # P1: 10♠, Q♠ (20)
    # D: 10♣, Q♣ (20)
    shoe_cards = [
        Card("10", "♠"), Card("10", "♣"), Card("Q", "♠"),
        Card("Q", "♣"),
    ]
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )
    result = cli.run(num_players=1, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.ACTIVE
    assert result.winner == Winner.PUSH
