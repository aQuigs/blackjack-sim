import pytest

from blackjack.cli import BlackjackCLI
from blackjack.entities.card import Card
from blackjack.entities.state import Outcome
from blackjack.strategy.base import Strategy
from tests.blackjack.conftest import parse_final_hands_and_outcomes


class AlwaysHitStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        from blackjack.action import Action

        return Action.HIT


class AlwaysStandStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        from blackjack.action import Action

        return Action.STAND


def test_shoe_exhaustion_raises_value_error():
    """Test that running out of cards in the shoe raises ValueError via CLI."""
    # Only enough cards for initial deal, player will try to hit but no cards left
    shoe_cards = [
        Card("10", "♠"),  # Player 1 first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player 1 second card
        Card("8", "♣"),  # Dealer second card
    ]

    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )

    with pytest.raises(ValueError, match="No more cards in the shoe"):
        cli.run(num_players=1, printable=False)


def test_blackjack_and_bust_are_reported():
    """Test that blackjack and bust outcomes are reported via CLI and event log."""

    class StandThenHitStrategy(Strategy):
        def __init__(self):
            self.called = False

        def choose_action(self, hand, available_actions, game_state):
            from blackjack.action import Action

            if not self.called:
                self.called = True
                return Action.STAND
            return Action.HIT

    # Player gets blackjack, dealer does not
    shoe_cards = [
        Card("A", "♠"),  # Player 1 first card
        Card("9", "♣"),  # Dealer first card
        Card("10", "♦"),  # Player 1 second card (blackjack)
        Card("8", "♣"),  # Dealer second card
    ]

    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=StandThenHitStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )

    cli.run(num_players=1, printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player 1"] == Outcome.BLACKJACK
    assert hands["Player 1"] == [Card("A", "♠"), Card("10", "♦")]
    assert hands["Dealer"] == [Card("9", "♣"), Card("8", "♣")]

    # Now test bust
    shoe_cards = [
        Card("10", "♠"),  # Player 1 first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player 1 second card
        Card("8", "♣"),  # Dealer second card
        Card("10", "♣"),  # Player hit (busts)
    ]

    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )

    cli.run(num_players=1, printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player 1"] == Outcome.BUST


def test_event_log_consistency_simple_game():
    """Test that the event log contains all expected events in order for a simple game."""
    event_log = []
    shoe_cards = [
        Card("10", "♠"),  # Player first
        Card("9", "♣"),  # Dealer first
        Card("7", "♦"),  # Player second
        Card("8", "♣"),  # Dealer second
        Card("4", "♠"),  # Player hit
    ]
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.run(num_players=1, printable=False)
    # Check event types in order
    event_types = [e.type.name for e in event_log]
    assert event_types[:4] == ["DEAL", "DEAL", "DEAL", "DEAL"]  # Initial deal
    assert "CHOOSE_ACTION" in event_types
    assert "HIT" in event_types
    assert any(e.type.name == "BUST" or e.type.name == "BLACKJACK" or e.type.name == "TWENTY_ONE" for e in event_log)


def test_invalid_action_raises_runtime_error():
    """Test that attempting an invalid action raises RuntimeError."""

    class InvalidActionStrategy(Strategy):
        def choose_action(self, hand, available_actions, game_state):
            from blackjack.action import Action

            return Action.GAME_END  # Not a valid action in this context

    shoe_cards = [
        Card("10", "♠"),  # Player first
        Card("9", "♣"),  # Dealer first
        Card("7", "♦"),  # Player second
        Card("8", "♣"),  # Dealer second
    ]
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=InvalidActionStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )
    with pytest.raises(RuntimeError, match="No valid action available"):
        cli.run(num_players=1, printable=False)
