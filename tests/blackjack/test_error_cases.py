import pytest

from blackjack.cli import BlackjackCLI
from blackjack.entities.card import Card
from blackjack.game_events import PlayerOutcome, Winner
from blackjack.strategy.base import Strategy


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

    result = cli.run(num_players=1, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.BLACKJACK
    assert result.winner == Winner.PLAYER

    blackjack_events = [e for e in event_log if e.type.name == "BLACKJACK"]
    assert len(blackjack_events) == 1
    assert blackjack_events[0].payload.player == "Player 1"

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

    result = cli.run(num_players=1, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.BUST

    bust_events = [e for e in event_log if e.type.name == "BUST"]
    assert len(bust_events) == 1
    assert bust_events[0].payload.player == "Player 1"
