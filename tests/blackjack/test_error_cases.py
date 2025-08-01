import pytest

from blackjack.cli import BlackjackService
from blackjack.entities.card import Card
from blackjack.entities.state import Outcome
from blackjack.game_events import GameEventType
from blackjack.strategy.base import Strategy
from blackjack.turn.action import Action
from tests.blackjack.conftest import parse_final_hands_and_outcomes


class AlwaysHitStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return Action.HIT


class AlwaysStandStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return Action.STAND


class InvalidActionStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return Action.NOOP  # Not a valid action in this context


def test_shoe_exhaustion_raises_value_error():
    """Test that running out of cards in the shoe raises ValueError via CLI."""
    # Only enough cards for initial deal, player will try to hit but no cards left
    shoe_cards = [
        Card("10", "♠"),  # Player 1 first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player 1 second card
        Card("8", "♣"),  # Dealer second card
    ]

    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )

    with pytest.raises(ValueError, match="No more cards in the shoe"):
        cli.play_games(printable=False)


def test_blackjack_and_bust_are_reported():
    """Test that blackjack and bust outcomes are reported via CLI and event log."""

    class StandThenHitStrategy(Strategy):
        def __init__(self):
            self.called = False

        def choose_action(self, hand, available_actions, game_state):
            from blackjack.turn.action import Action

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
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=StandThenHitStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.BLACKJACK
    assert hands["Player"] == [Card("A", "♠"), Card("10", "♦")]
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
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE


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
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    # Check event types in order
    event_types = [e.event_type for e in event_log]
    assert event_types[:4] == [GameEventType.DEAL] * 4
    assert GameEventType.CHOOSE_ACTION in event_types
    assert GameEventType.HIT in event_types
    assert any(
        e.event_type == GameEventType.BUST
        or e.event_type == GameEventType.BLACKJACK
        or e.event_type == GameEventType.TWENTY_ONE
        for e in event_log
    )


def test_invalid_action_raises_runtime_error():
    """Test that attempting an invalid action raises RuntimeError."""

    shoe_cards = [
        Card("10", "♠"),  # Player first
        Card("9", "♣"),  # Dealer first
        Card("7", "♦"),  # Player second
        Card("8", "♣"),  # Dealer second
    ]
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=InvalidActionStrategy(),
        dealer_strategy=AlwaysStandStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )
    with pytest.raises(RuntimeError, match="Invalid action Action.NOOP for player Player"):
        cli.play_games(printable=False)
