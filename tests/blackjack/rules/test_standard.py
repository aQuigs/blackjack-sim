from app.src.blackjack.rules.standard import StandardBlackjackRules
from app.src.blackjack.entities.hand import Hand
from app.src.blackjack.entities.card import Card
from app.src.blackjack.action import Action


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
    # Dealer hits on 16
    hand = make_hand([("10", "♠"), ("6", "♣")])
    assert rules.dealer_should_hit(hand)
    # Dealer stands on hard 17
    hand = make_hand([("10", "♠"), ("7", "♣")])
    assert not rules.dealer_should_hit(hand)
    # Dealer stands on soft 17
    hand = make_hand([("A", "♠"), ("6", "♣")])
    assert not rules.dealer_should_hit(hand)


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
