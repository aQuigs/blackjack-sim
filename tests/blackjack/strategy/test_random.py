import pytest

from blackjack.action import Action
from blackjack.entities.hand import Hand
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
