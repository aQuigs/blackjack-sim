import pytest

from blackjack.action import Action
from blackjack.cli import BlackjackCLI
from blackjack.entities.card import Card
from blackjack.entities.hand import Hand
from blackjack.game_events import PlayerOutcome, Winner
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.base import Strategy
from blackjack.strategy.strategy import StandardDealerStrategy


def make_hand(cards):
    hand = Hand()
    for rank, suit in cards:
        hand.add_card(Card(rank, suit))
    return hand


def test_hand_value_hard_and_soft():
    rules = StandardBlackjackRules()
    # Hard 17
    hand = make_hand([("10", "♠"), ("7", "♣")])
    hv = rules.hand_value(hand)
    assert hv.value == 17
    assert not hv.soft
    # Soft 17
    hand = make_hand([("A", "♠"), ("6", "♣")])
    hv = rules.hand_value(hand)
    assert hv.value == 17
    assert hv.soft
    # Soft 13, then hard 13 after drawing 10
    hand = make_hand([("A", "♠"), ("2", "♣")])
    hv = rules.hand_value(hand)
    assert hv.value == 13
    assert hv.soft
    hand.add_card(Card("10", "♦"))
    hv = rules.hand_value(hand)
    assert hv.value == 13
    assert not hv.soft


def test_is_blackjack():
    rules = StandardBlackjackRules()
    hand = make_hand([("A", "♠"), ("K", "♣")])
    assert rules.is_blackjack(hand)
    hand = make_hand([("A", "♠"), ("9", "♣"), ("A", "♦")])
    assert not rules.is_blackjack(hand)


def test_is_bust():
    rules = StandardBlackjackRules()
    hand = make_hand([("10", "♠"), ("9", "♣"), ("5", "♦")])
    assert rules.is_bust(hand)
    hand = make_hand([("A", "♠"), ("9", "♣"), ("A", "♦")])
    assert not rules.is_bust(hand)


def test_dealer_should_hit():
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    # Dealer hits on 16
    hand = make_hand([("10", "♠"), ("6", "♣")])
    actions = rules.available_actions(hand, {})
    action = dealer_strategy.choose_action(hand, actions, {})
    assert action == Action.HIT
    # Dealer stands on hard 17
    hand = make_hand([("10", "♠"), ("7", "♣")])
    actions = rules.available_actions(hand, {})
    action = dealer_strategy.choose_action(hand, actions, {})
    assert action == Action.STAND
    # Dealer stands on soft 17
    hand = make_hand([("A", "♠"), ("6", "♣")])
    actions = rules.available_actions(hand, {})
    action = dealer_strategy.choose_action(hand, actions, {})
    assert action == Action.STAND


def test_blackjack_payout():
    rules = StandardBlackjackRules()
    assert rules.blackjack_payout() == 1.5


def test_handvalue_str_and_repr():
    from blackjack.rules.base import HandValue

    hv = HandValue(17, True)
    assert str(hv) == "17, soft"
    assert "HandValue(value=17, soft=True)" in repr(hv)


def test_rules_base_not_implemented():
    from blackjack.rules.base import Rules

    class DummyRules(Rules):
        pass

    rules = DummyRules()
    from blackjack.entities.hand import Hand

    hand = Hand()

    with pytest.raises(NotImplementedError):
        rules.hand_value(hand)
    with pytest.raises(NotImplementedError):
        rules.is_blackjack(hand)
    with pytest.raises(NotImplementedError):
        rules.is_bust(hand)
    with pytest.raises(NotImplementedError):
        rules.dealer_should_hit(hand)
    with pytest.raises(NotImplementedError):
        rules.blackjack_payout()
    with pytest.raises(NotImplementedError):
        rules.available_actions(hand, {})
    with pytest.raises(NotImplementedError):
        rules.can_continue(hand, {})


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
        Card("9", "♣"),
        Card("K", "♠"),
        Card("8", "♣"),
        Card("2", "♦"),  # Extra cards for safety
        Card("3", "♠"),
    ]
    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    result = cli.run(num_players=1, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.BLACKJACK
    assert result.winner == Winner.PLAYER
    assert result.player_results[0].hand == [Card("A", "♠"), Card("K", "♠")]
    assert result.dealer_hand == [Card("9", "♣"), Card("8", "♣")]
    player_events = [e for e in event_log if getattr(e.payload, "player", None) == "Player 1"]
    assert any(e.type.name == "BLACKJACK" for e in player_events)


def test_bust_detection():
    # Player busts, dealer wins
    shoe_cards = [
        Card("10", "♠"),
        Card("9", "♣"),
        Card("5", "♦"),
        Card("8", "♣"),
        Card("7", "♠"),  # Player will hit and bust
        Card("2", "♦"),  # Dealer extra
    ]
    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    result = cli.run(num_players=1, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.BUST
    assert result.winner == Winner.DEALER
    assert result.player_results[0].hand == [Card("10", "♠"), Card("5", "♦"), Card("7", "♠")]
    assert result.dealer_hand == [Card("9", "♣"), Card("8", "♣")]
    player_events = [e for e in event_log if getattr(e.payload, "player", None) == "Player 1"]
    assert any(e.type.name == "BUST" for e in player_events)


def test_dealer_hits_on_16_stands_on_17():
    # Dealer hits on 16, stands on 17
    # Player stands on 12, dealer: 10, 6 (hits 2 for 18)
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("6", "♣"),
        Card("2", "♠"),
        Card("3", "♦"),  # Dealer extra
        Card("4", "♥"),  # More dealer extra
        Card("5", "♠"),  # More dealer extra
    ]
    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    result = cli.run(num_players=1, printable=False)
    assert result.winner == Winner.DEALER
    assert result.player_results[0].hand == [Card("10", "♠"), Card("6", "♣")]
    assert result.dealer_hand == [Card("10", "♣"), Card("2", "♠"), Card("3", "♦"), Card("4", "♥")]
    dealer_events = [e for e in event_log if getattr(e.payload, "player", None) == "Dealer"]
    assert any(e.type.name == "HIT" for e in dealer_events)
    assert any(
        e.type.name == "STAND" or (hasattr(e.payload, "action") and e.payload.action.name == "STAND")
        for e in dealer_events
    )


def test_available_actions_and_can_continue():
    # Player gets 10, 6 (can hit or stand), then busts
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("6", "♣"),
        Card("7", "♠"),
        Card("8", "♦"),  # Player will hit and bust
        Card("2", "♣"),  # Dealer extra
    ]
    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    result = cli.run(num_players=1, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.BUST
    assert result.player_results[0].hand == [Card("10", "♠"), Card("6", "♣"), Card("8", "♦")]
    assert result.dealer_hand == [Card("10", "♣"), Card("7", "♠")]
    player_events = [e for e in event_log if getattr(e.payload, "player", None) == "Player 1"]
    assert any(e.type.name == "BUST" for e in player_events)
