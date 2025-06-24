import random

from blackjack.action import Action
from blackjack.entities.hand import Hand
from blackjack.strategy.base import PlayerStrategy


class RandomStrategy(PlayerStrategy):
    def choose_action(
        self, hand: Hand, available_actions: list[Action], game_state: dict
    ) -> Action:
        if not available_actions:
            raise ValueError("No available actions to choose from.")
        return random.choice(available_actions)
