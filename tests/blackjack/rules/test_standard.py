from blackjack.action import Action
from blackjack.entities.card import Card
from blackjack.entities.hand import Hand
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.random import StandardDealerStrategy


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


def test_available_actions_and_can_continue():
    rules = StandardBlackjackRules()
    hand = make_hand([("10", "♠"), ("6", "♣")])
    actions = rules.available_actions(hand, {})
    assert Action.HIT in actions and Action.STAND in actions
    assert rules.can_continue(hand, {})
    # Bust
    hand = make_hand([("10", "♠"), ("9", "♣"), ("5", "♦")])
    actions = rules.available_actions(hand, {})
    assert actions == []
    assert not rules.can_continue(hand, {})


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
    import pytest

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
