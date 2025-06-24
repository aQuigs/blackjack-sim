import pytest
from app.src.blackjack.strategy.random import RandomStrategy
from app.src.blackjack.entities.hand import Hand
from app.src.blackjack.action import Action


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
