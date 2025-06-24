from blackjack.action import Action
from blackjack.entities.hand import Hand


class Strategy:
    def choose_action(self, hand: Hand, available_actions: list[Action], game_state: dict) -> Action:
        raise NotImplementedError
