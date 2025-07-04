from blackjack.cli import BlackjackService
from blackjack.entities.card import Card
from blackjack.entities.state import Outcome
from blackjack.game_events import GameEventType
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.base import Strategy
from blackjack.turn.action import Action
from tests.blackjack.conftest import parse_final_hands_and_outcomes


class AlwaysSplitStrategy(Strategy):

    def choose_action(self, hand, available_actions, game_state):
        if Action.SPLIT in available_actions:
            return Action.SPLIT
        if Action.HIT in available_actions:
            return Action.HIT
        return Action.STAND


class AlwaysStandStrategy(Strategy):

    def choose_action(self, hand, available_actions, game_state):
        return Action.STAND


def padded_shoe(cards, n=50):
    return cards + [Card("2", "♣")] * n


def count_player_hands(event_log):
    return sum(1 for e in event_log if e.event_type == GameEventType.ROUND_RESULT and e.name == "Player")


def get_player_hands(event_log):
    return [e.hand for e in event_log if e.event_type == GameEventType.ROUND_RESULT and e.name == "Player"]


def test_regular_split():
    # Player: 8♦, 8♣; Dealer: 10♦, 10♠
    event_log = []
    shoe_cards = padded_shoe(
        [Card("8", "♦"), Card("10", "♦"), Card("8", "♣"), Card("10", "♠"), Card("2", "♠"), Card("3", "♣")]
    )
    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysSplitStrategy(),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    assert count_player_hands(event_log) == 2


def test_invalid_split():
    # Player: 7♦, 8♣; Dealer: 10♦, 10♠
    event_log = []
    shoe_cards = padded_shoe([Card("7", "♦"), Card("10", "♦"), Card("8", "♣"), Card("10", "♠")])
    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysSplitStrategy(),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    assert count_player_hands(event_log) == 1


def test_split_aces():
    # Player: A♦, A♣; Dealer: 10♦, 10♠
    event_log = []
    shoe_cards = padded_shoe(
        [Card("A", "♦"), Card("10", "♦"), Card("A", "♣"), Card("10", "♠"), Card("2", "♠"), Card("3", "♣")]
    )
    rules = StandardBlackjackRules(resplit_aces=False, play_split_aces=False)
    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysSplitStrategy(),
        output_tracker=event_log.append,
        rules=rules,
    )
    cli.play_games(printable=False)
    assert count_player_hands(event_log) == 2


def test_split_aces_get_21():
    # Player: A♦, A♣; Dealer: 10♦, 10♠; Next: 10♥, 10♣
    event_log = []
    shoe_cards = padded_shoe(
        [Card("A", "♦"), Card("10", "♦"), Card("A", "♣"), Card("10", "♠"), Card("10", "♥"), Card("10", "♣")]
    )
    rules = StandardBlackjackRules(resplit_aces=False, play_split_aces=False)
    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysSplitStrategy(),
        output_tracker=event_log.append,
        rules=rules,
    )
    cli.play_games(printable=False)
    for hand in get_player_hands(event_log):
        ranks = set(card.rank for card in hand)
        if ranks == {"A", "10"}:
            hands, outcomes = parse_final_hands_and_outcomes(event_log)
            assert outcomes["Player"] != Outcome.BLACKJACK


def test_split_10s_get_21():
    # Player: 10♦, 10♣; Dealer: A♦, A♠; Next: A♣, 10♥
    event_log = []
    shoe_cards = padded_shoe(
        [Card("10", "♦"), Card("A", "♦"), Card("10", "♣"), Card("A", "♠"), Card("A", "♣"), Card("10", "♥")]
    )
    rules = StandardBlackjackRules()
    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysSplitStrategy(),
        output_tracker=event_log.append,
        rules=rules,
    )
    cli.play_games(printable=False)
    for hand in get_player_hands(event_log):
        ranks = set(card.rank for card in hand)
        if ranks == {"A", "10"}:
            hands, outcomes = parse_final_hands_and_outcomes(event_log)
            assert outcomes["Player"] != Outcome.BLACKJACK


def test_resplit_aces_allowed():
    # Player: A♦, A♣; Dealer: 10♦, 10♠; Next: A♥, A♠, A♣, A♥ (for more than max splits), 2♠, 3♣
    event_log = []
    shoe_cards = padded_shoe(
        [
            Card("A", "♦"),
            Card("10", "♦"),
            Card("A", "♣"),
            Card("10", "♠"),
            Card("A", "♥"),
            Card("A", "♠"),
            Card("A", "♣"),
            Card("A", "♥"),
            Card("2", "♠"),
            Card("3", "♣"),
        ]
    )
    rules = StandardBlackjackRules(resplit_aces=True, play_split_aces=False)
    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysSplitStrategy(),
        output_tracker=event_log.append,
        rules=rules,
    )
    cli.play_games(printable=False)
    assert count_player_hands(event_log) == 4


def test_resplit_aces_not_allowed():
    # Player: A♦, A♣; Dealer: 10♦, 10♠; Next: A♥, 2♠, 3♣
    event_log = []
    shoe_cards = padded_shoe(
        [
            Card("A", "♦"),
            Card("10", "♦"),
            Card("A", "♣"),
            Card("10", "♠"),
            Card("A", "♥"),
            Card("2", "♠"),
            Card("3", "♣"),
        ]
    )
    rules = StandardBlackjackRules(resplit_aces=False, play_split_aces=False)
    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysSplitStrategy(),
        output_tracker=event_log.append,
        rules=rules,
    )
    cli.play_games(printable=False)
    assert count_player_hands(event_log) == 2


def test_resplit_non_aces():
    # Player: 8♦, 8♣; Dealer: 10♦, 10♠; Next: 8♥, 8♠, 8♣, 8♥ (for more than max splits), 2♠, 3♣
    event_log = []
    shoe_cards = padded_shoe(
        [
            Card("8", "♦"),
            Card("10", "♦"),
            Card("8", "♣"),
            Card("10", "♠"),
            Card("8", "♥"),
            Card("8", "♠"),
            Card("8", "♣"),
            Card("8", "♥"),
            Card("2", "♠"),
            Card("3", "♣"),
        ]
    )
    rules = StandardBlackjackRules(max_splits=3)
    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysSplitStrategy(),
        output_tracker=event_log.append,
        rules=rules,
    )
    cli.play_games(printable=False)
    assert count_player_hands(event_log) == 4


def test_maximum_splits_reached():
    # Player: 8♦, 8♣; Dealer: 10♦, 10♠; Next: 8♥, 8♠ (for resplits), 2♠, 3♣
    event_log = []
    shoe_cards = padded_shoe(
        [
            Card("8", "♦"),
            Card("10", "♦"),
            Card("8", "♣"),
            Card("10", "♠"),
            Card("8", "♥"),
            Card("8", "♠"),
            Card("2", "♠"),
            Card("3", "♣"),
        ]
    )
    rules = StandardBlackjackRules(max_splits=2)
    cli = BlackjackService.create_null(
        shoe_cards=list(reversed(shoe_cards)),
        player_strategy=AlwaysSplitStrategy(),
        output_tracker=event_log.append,
        rules=rules,
    )
    cli.play_games(printable=False)
    assert count_player_hands(event_log) == 3
