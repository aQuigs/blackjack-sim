import pytest

from blackjack.action import Action
from blackjack.entities.card import Card
from blackjack.entities.hand import Hand
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.base import Strategy
from blackjack.strategy.random import RandomStrategy


def test_random_strategy_chooses_action():
    strategy = RandomStrategy()
    hand = Hand()
    actions = [Action.HIT, Action.STAND]
    # Should always return one of the available actions
    for _ in range(10):
        action = strategy.choose_action(hand, actions, {})
        assert action in actions


def test_random_strategy_empty_actions():
    strategy = RandomStrategy()
    hand = Hand()
    with pytest.raises(ValueError):
        strategy.choose_action(hand, [], {})


def test_random_strategy_raises_on_no_actions():
    strategy = RandomStrategy()
    hand = Hand()
    with pytest.raises(ValueError):
        strategy.choose_action(hand, [], {})


def test_strategy_not_implemented():
    class DummyStrategy(Strategy):
        pass

    s = DummyStrategy()
    with pytest.raises(NotImplementedError):
        s.choose_action(None, [], {})


def test_standard_dealer_strategy_choices():
    from blackjack.strategy.random import StandardDealerStrategy

    dealer_strategy = StandardDealerStrategy()
    rules = StandardBlackjackRules()
    # Dealer should hit on 16
    hand = Hand()
    hand.add_card(Card("10", "♠"))
    hand.add_card(Card("6", "♣"))
    actions = rules.available_actions(hand, {})
    assert dealer_strategy.choose_action(hand, actions, {}) == Action.HIT
    # Dealer should stand on 17
    hand = Hand()
    hand.add_card(Card("10", "♠"))
    hand.add_card(Card("7", "♣"))
    actions = rules.available_actions(hand, {})
    assert dealer_strategy.choose_action(hand, actions, {}) == Action.STAND


def test_random_strategy_one_action():
    strategy = RandomStrategy()
    hand = Hand()
    action = strategy.choose_action(hand, [Action.STAND], {})
    assert action == Action.STAND
