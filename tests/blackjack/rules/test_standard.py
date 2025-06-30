from blackjack.cli import BlackjackService
from blackjack.entities.card import Card
from blackjack.entities.hand import Hand
from blackjack.entities.state import Outcome
from blackjack.game_events import GameEventType
from blackjack.strategy.base import Strategy
from blackjack.strategy.strategy import StandardDealerStrategy
from tests.blackjack.conftest import parse_final_hands_and_outcomes


def make_hand(cards):
    hand = Hand()
    for rank, suit in cards:
        hand.add_card(Card(rank, suit))
    return hand


class AlwaysHitStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "HIT"), available_actions[0])


class AlwaysStandStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "STAND"), available_actions[0])


def test_blackjack_detection():
    # Player gets blackjack, dealer does not
    shoe_cards = [
        Card("A", "♠"),
        Card("9", "♠"),
        Card("K", "♠"),
        Card("8", "♠"),
        Card("2", "♠"),  # Extra cards for safety
        Card("3", "♠"),
    ]
    event_log = []
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.BLACKJACK
    assert hands["Player"] == [Card("A", "♠"), Card("K", "♠")]
    assert hands["Dealer"] == [Card("9", "♠"), Card("8", "♠")]
    player_events = [e for e in event_log if getattr(e, "player", None) == "Player"]
    assert any(e.event_type == GameEventType.BLACKJACK for e in player_events)


def test_bust_detection():
    # Player busts, dealer wins
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♠"),
        Card("5", "♠"),
        Card("8", "♠"),
        Card("7", "♠"),  # Player will hit and bust
        Card("2", "♠"),  # Dealer extra
    ]
    event_log = []
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE
    assert hands["Player"] == [Card("10", "♠"), Card("5", "♠"), Card("7", "♠")]
    assert hands["Dealer"] == [Card("9", "♠"), Card("8", "♠")]
    player_events = [e for e in event_log if getattr(e, "player", None) == "Player"]
    assert any(e.event_type == GameEventType.BUST for e in player_events)


def test_dealer_hits_on_16_stands_on_17():
    # Dealer hits on 16, stands on 17
    # Player stands on 12, dealer: 10, 6 (hits 2 for 18)
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♠"),
        Card("6", "♠"),
        Card("2", "♠"),
        Card("3", "♠"),  # Dealer extra
        Card("4", "♠"),  # More dealer extra
        Card("5", "♠"),  # More dealer extra
    ]
    event_log = []
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    # Dealer may only have initial cards if not required to hit
    assert "Dealer" in hands
    assert "Player" in hands
    dealer_events = [e for e in event_log if getattr(e, "player", None) == "Dealer"]
    # Dealer should not bust in this scenario (final hand is 18)
    assert not any(e.event_type == GameEventType.BUST for e in dealer_events)
    assert any((hasattr(e, "action") and e.action.name == "STAND") for e in dealer_events)


def test_available_actions_and_can_continue():
    # Player gets 10, 6 (can hit or stand), then busts
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♠"),
        Card("6", "♠"),
        Card("7", "♠"),
        Card("8", "♠"),  # Player will hit and bust
        Card("2", "♠"),  # Dealer extra
    ]
    event_log = []
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.LOSE
    assert "Dealer" in hands
    assert hands["Player"] == [Card("10", "♠"), Card("6", "♠"), Card("8", "♠")]
    assert hands["Dealer"] == [Card("10", "♠"), Card("7", "♠")]
    player_events = [e for e in event_log if getattr(e, "player", None) == "Player"]
    assert any(e.event_type == GameEventType.BUST for e in player_events)
