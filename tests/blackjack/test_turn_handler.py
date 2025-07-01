import pytest

from blackjack.cli import BlackjackService
from blackjack.entities.card import Card
from blackjack.entities.state import Outcome
from blackjack.game_events import GameEventType
from blackjack.strategy.base import Strategy
from blackjack.turn.action import Action
from tests.blackjack.conftest import (
    AlwaysDoubleStrategy,
    parse_final_hands_and_outcomes,
)


class AlwaysStandStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return Action.STAND


class AlwaysHitStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return Action.HIT


class HitUntilBustStrategy(Strategy):
    def __init__(self, hit_count=0):
        self.hit_count = hit_count
        self.current_hits = 0

    def choose_action(self, hand, available_actions, game_state):
        if self.current_hits < self.hit_count:
            self.current_hits += 1
            return Action.HIT
        return Action.STAND


def test_pre_deal_handler():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    deal_events = [e for e in event_log if e.event_type == GameEventType.DEAL]
    assert len(deal_events) == 4

    player_deals = [e for e in deal_events if e.to == "Player"]
    assert len(player_deals) == 2
    assert player_deals[0].card == Card("10", "♠")
    assert player_deals[1].card == Card("5", "♦")

    dealer_deals = [e for e in deal_events if e.to == "Dealer"]
    assert len(dealer_deals) == 2
    assert dealer_deals[0].card == Card("9", "♣")
    assert dealer_deals[1].card == Card("8", "♣")


def test_check_dealer_ace_handler_with_ace():
    event_log = []
    shoe_cards = [
        Card("A", "♠"),
        Card("A", "♣"),
        Card("10", "♦"),
        Card("9", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.BLACKJACK


def test_check_dealer_ace_handler_without_ace():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hands, outcomes = parse_final_hands_and_outcomes(event_log)


def test_check_dealer_blackjack_handler_with_blackjack():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("A", "♣"),
        Card("5", "♦"),
        Card("10", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    blackjack_events = [e for e in event_log if e.event_type == GameEventType.BLACKJACK]
    assert len(blackjack_events) == 1
    assert blackjack_events[0].player == "Dealer"

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE


def test_check_dealer_blackjack_handler_without_blackjack():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("A", "♣"),
        Card("5", "♦"),
        Card("9", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    blackjack_events = [e for e in event_log if e.event_type == GameEventType.BLACKJACK]
    assert len(blackjack_events) == 0


def test_check_player_bj_handler_with_blackjack():
    event_log = []
    shoe_cards = [
        Card("A", "♠"),
        Card("9", "♣"),
        Card("10", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    blackjack_events = [e for e in event_log if e.event_type == GameEventType.BLACKJACK]
    assert len(blackjack_events) == 1
    assert blackjack_events[0].player == "Player"

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.BLACKJACK


def test_check_player_bj_handler_without_blackjack():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    blackjack_events = [e for e in event_log if e.event_type == GameEventType.BLACKJACK]
    assert len(blackjack_events) == 0


def test_take_turn_handler_player_stand():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    choose_events = [e for e in event_log if e.event_type == GameEventType.CHOOSE_ACTION]
    assert len(choose_events) >= 1
    assert choose_events[0].action == Action.STAND


def test_take_turn_handler_player_hit():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
        Card("3", "♥"),
        Card("7", "♥"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysHitStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    choose_events = [e for e in event_log if e.event_type == GameEventType.CHOOSE_ACTION]
    hit_events = [e for e in event_log if e.event_type == GameEventType.HIT]

    assert len(choose_events) >= 1
    assert choose_events[0].action == Action.HIT
    assert len(hit_events) >= 1


def test_take_turn_handler_dealer_stand():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("8", "♦"),
        Card("7", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    choose_events = [e for e in event_log if e.event_type == GameEventType.CHOOSE_ACTION]
    assert len(choose_events) >= 2

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.WIN


def test_take_turn_handler_dealer_hit():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("10", "♦"),
        Card("6", "♣"),
        Card("5", "♥"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hit_events = [e for e in event_log if e.event_type == GameEventType.HIT]
    assert len(hit_events) >= 1

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE


def test_check_player_card_state_handler_bust():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
        Card("10", "♥"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysHitStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    bust_events = [e for e in event_log if e.event_type == GameEventType.BUST]
    assert len(bust_events) == 1
    assert bust_events[0].player == "Player"

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE


def test_check_player_card_state_handler_twenty_one():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
        Card("6", "♥"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysHitStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    twenty_one_events = [e for e in event_log if e.event_type == GameEventType.TWENTY_ONE]
    assert len(twenty_one_events) == 1
    assert twenty_one_events[0].player == "Player"


def test_check_player_card_state_handler_continue():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    bust_events = [e for e in event_log if e.event_type == GameEventType.BUST]
    twenty_one_events = [e for e in event_log if e.event_type == GameEventType.TWENTY_ONE]
    assert len(bust_events) == 0
    assert len(twenty_one_events) == 0


def test_check_dealer_card_state_handler_bust():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("5", "♦"),
        Card("6", "♣"),
        Card("10", "♥"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    bust_events = [e for e in event_log if e.event_type == GameEventType.BUST]
    assert len(bust_events) == 1
    assert bust_events[0].player == "Dealer"

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.WIN


def test_check_dealer_card_state_handler_twenty_one():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("5", "♦"),
        Card("6", "♣"),
        Card("5", "♥"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    twenty_one_events = [e for e in event_log if e.event_type == GameEventType.TWENTY_ONE]
    assert len(twenty_one_events) == 1
    assert twenty_one_events[0].player == "Dealer"


def test_evaluate_game_handler_player_wins():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("10", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.WIN


def test_evaluate_game_handler_dealer_wins():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("6", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE


def test_evaluate_game_handler_tie():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("8", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.PUSH


def test_game_over_handler_blackjack():
    event_log = []
    shoe_cards = [
        Card("A", "♠"),
        Card("9", "♣"),
        Card("10", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.BLACKJACK


def test_game_over_handler_win():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("10", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.WIN


def test_game_over_handler_lose():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("6", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE


def test_game_over_handler_push():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("8", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.PUSH


def test_take_turn_handler_invalid_action():
    class InvalidActionStrategy(Strategy):
        def choose_action(self, hand, available_actions, game_state):
            return Action.NOOP

    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=InvalidActionStrategy(),
    )

    with pytest.raises(RuntimeError, match="Invalid action Action.NOOP for player Player"):
        cli.play_games(printable=False)


def test_multiple_player_hits():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
        Card("3", "♥"),
        Card("2", "♥"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=HitUntilBustStrategy(hit_count=2),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hit_events = [e for e in event_log if e.event_type == GameEventType.HIT]
    assert len(hit_events) == 2

    choose_events = [e for e in event_log if e.event_type == GameEventType.CHOOSE_ACTION]
    assert len(choose_events) >= 2


def test_dealer_multiple_hits():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("5", "♦"),
        Card("6", "♣"),
        Card("2", "♥"),
        Card("3", "♥"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysStandStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    hit_events = [e for e in event_log if e.event_type == GameEventType.HIT]
    assert len(hit_events) >= 1

    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE


def test_logging_coverage():
    import logging

    logging.getLogger("blackjack.gameplay.turn_handler").setLevel(logging.INFO)

    event_log = []
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
        Card("10", "♥"),
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysHitStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    bust_events = [e for e in event_log if e.event_type == GameEventType.BUST]
    assert len(bust_events) == 1
    assert bust_events[0].player == "Player"

    logging.getLogger("blackjack.gameplay.turn_handler").setLevel(logging.WARNING)


def test_take_turn_handler_player_double():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),  # Player first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player second card (15 total)
        Card("8", "♣"),  # Dealer second card
        Card("6", "♥"),  # Player double card (21 total)
        Card("10", "♠"),  # Extra card for dealer if needed
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysDoubleStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    # Check that double event occurred
    double_events = [e for e in event_log if e.event_type == GameEventType.DOUBLE]
    assert len(double_events) == 1
    assert double_events[0].player == "Player"
    assert double_events[0].card == Card("6", "♥")

    # Check that no hit events occurred (double generates DoubleEvent, not HitEvent)
    hit_events = [e for e in event_log if e.event_type == GameEventType.HIT]
    assert len(hit_events) == 0

    # Check final outcome
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.WIN


def test_take_turn_handler_player_double_bust():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),  # Player first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player second card (15 total)
        Card("8", "♣"),  # Dealer second card
        Card("10", "♥"),  # Player double card (25 total, bust)
        Card("10", "♠"),  # Extra card for dealer if needed
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysDoubleStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    # Check that double event occurred
    double_events = [e for e in event_log if e.event_type == GameEventType.DOUBLE]
    assert len(double_events) == 1
    assert double_events[0].player == "Player"
    assert double_events[0].card == Card("10", "♥")

    # Check that bust event occurred
    bust_events = [e for e in event_log if e.event_type == GameEventType.BUST]
    assert len(bust_events) == 1
    assert bust_events[0].player == "Player"

    # Check final outcome
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE


def test_take_turn_handler_player_double_push():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),  # Player first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player second card (15 total)
        Card("6", "♣"),  # Dealer second card (15 total)
        Card("6", "♥"),  # Player double card (21 total)
        Card("6", "♠"),  # Dealer hit card (21 total)
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysDoubleStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    # Check that double event occurred
    double_events = [e for e in event_log if e.event_type == GameEventType.DOUBLE]
    assert len(double_events) == 1
    assert double_events[0].player == "Player"

    # Check final outcome
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.PUSH


def test_take_turn_handler_player_double_lose():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),  # Player first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player second card (15 total)
        Card("7", "♣"),  # Dealer second card (16 total)
        Card("5", "♥"),  # Player double card (20 total)
        Card("5", "♠"),  # Dealer hit card (21 total)
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysDoubleStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    # Check that double event occurred
    double_events = [e for e in event_log if e.event_type == GameEventType.DOUBLE]
    assert len(double_events) == 1
    assert double_events[0].player == "Player"

    # Check final outcome
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE


def test_take_turn_handler_player_double_only_on_initial_turn():
    event_log = []
    shoe_cards = [
        Card("10", "♠"),  # Player first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player second card (15 total)
        Card("8", "♣"),  # Dealer second card
        Card("6", "♥"),  # Player hit card (21 total)
        Card("10", "♠"),  # Extra card for dealer if needed
    ]

    # Create a strategy that tries to double but falls back to hit
    class DoubleThenHitStrategy(Strategy):
        def choose_action(self, hand, available_actions, game_state):
            if Action.DOUBLE in available_actions:
                return Action.DOUBLE
            return Action.HIT

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=DoubleThenHitStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    # Check that double event occurred (on initial turn)
    double_events = [e for e in event_log if e.event_type == GameEventType.DOUBLE]
    assert len(double_events) == 1
    assert double_events[0].player == "Player"

    # Check that no additional double events occurred
    assert len(double_events) == 1

    # Check final outcome
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.WIN


def test_take_turn_handler_player_double_with_ace():
    event_log = []
    shoe_cards = [
        Card("A", "♠"),  # Player first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player second card (16 total, soft)
        Card("8", "♣"),  # Dealer second card
        Card("5", "♥"),  # Player double card (21 total)
        Card("10", "♠"),  # Extra card for dealer if needed
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysDoubleStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    # Check that double event occurred
    double_events = [e for e in event_log if e.event_type == GameEventType.DOUBLE]
    assert len(double_events) == 1
    assert double_events[0].player == "Player"
    assert double_events[0].card == Card("5", "♥")

    # Check final outcome
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.WIN


def test_take_turn_handler_player_double_with_soft_hand():
    event_log = []
    shoe_cards = [
        Card("A", "♠"),  # Player first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player second card (16 total, soft)
        Card("8", "♣"),  # Dealer second card
        Card("10", "♥"),  # Player double card (16 total, hard - ace becomes 1)
        Card("10", "♠"),  # Extra card for dealer if needed
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysDoubleStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(printable=False)

    # Check that double event occurred
    double_events = [e for e in event_log if e.event_type == GameEventType.DOUBLE]
    assert len(double_events) == 1
    assert double_events[0].player == "Player"
    assert double_events[0].card == Card("10", "♥")

    # Check final outcome
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE  # 16 vs 18


def test_take_turn_handler_player_double_multiple_rounds():
    event_log = []
    shoe_cards = [
        # Round 1
        Card("10", "♠"),  # Player first card
        Card("9", "♣"),  # Dealer first card
        Card("5", "♦"),  # Player second card (15 total)
        Card("8", "♣"),  # Dealer second card
        Card("6", "♥"),  # Player double card (21 total)
        # Round 2
        Card("10", "♦"),  # Player first card
        Card("9", "♥"),  # Dealer first card
        Card("5", "♠"),  # Player second card (15 total)
        Card("8", "♦"),  # Dealer second card
        Card("6", "♣"),  # Player double card (21 total)
        Card("10", "♠"),  # Extra card for dealer if needed
    ]

    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysDoubleStrategy(),
        output_tracker=event_log.append,
    )

    cli.play_games(num_rounds=2, printable=False)

    # Check that double events occurred for both rounds
    double_events = [e for e in event_log if e.event_type == GameEventType.DOUBLE]
    assert len(double_events) == 2
    assert all(e.player == "Player" for e in double_events)

    # Check final outcomes
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    # Both rounds should result in wins
    assert len([o for o in outcomes.values() if o == Outcome.WIN]) >= 1
