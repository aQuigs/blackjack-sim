import random

from blackjack.action import Action
from blackjack.entities.hand import Hand
from blackjack.strategy.base import Strategy


class RandomStrategy(Strategy):
    def choose_action(self, hand: Hand, available_actions: list[Action], game_state: dict) -> Action:
        if not available_actions:
            raise ValueError("No available actions to choose from.")
        return random.choice(available_actions)


class StandardDealerStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        from blackjack.rules.standard import StandardBlackjackRules

        rules = StandardBlackjackRules()
        hv = rules.hand_value(hand)
        if hv.value < 17 and Action.HIT in available_actions:
            return Action.HIT
        if Action.STAND in available_actions:
            return Action.STAND
        return available_actions[0]
