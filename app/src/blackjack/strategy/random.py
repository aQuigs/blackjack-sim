import random
from app.src.blackjack.strategy.base import PlayerStrategy
from app.src.blackjack.entities.hand import Hand
from app.src.blackjack.action import Action


class RandomStrategy(PlayerStrategy):
    def choose_action(self, hand: Hand, available_actions: list[Action], game_state: dict) -> Action:
        if not available_actions:
            raise ValueError("No available actions to choose from.")
        return random.choice(available_actions)
