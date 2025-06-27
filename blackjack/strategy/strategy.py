from typing import Union

from blackjack.action import Action
from blackjack.entities.hand import Hand
from blackjack.entities.random_wrapper import RandomWrapper
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.base import Strategy


class RandomStrategy(Strategy):
    def __init__(self, random_wrapper: Union[RandomWrapper, None] = None):
        self.randomizer = random_wrapper or RandomWrapper()

    def choose_action(self, hand: Hand, available_actions: list[Action], game_state: dict[str, object]) -> Action:
        if not available_actions:
            raise ValueError("No available actions to choose from.")

        return self.randomizer.choice(available_actions)


class StandardDealerStrategy(Strategy):
    def choose_action(self, hand: Hand, available_actions: list[Action], game_state: dict[str, object]) -> Action:
        rules = StandardBlackjackRules()
        hv = rules.hand_value(hand)

        if hv.value < 17 and Action.HIT in available_actions:
            return Action.HIT

        if Action.STAND in available_actions:
            return Action.STAND

        return available_actions[0]
