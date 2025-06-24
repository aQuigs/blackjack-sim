from app.src.blackjack.action import Action
from app.src.blackjack.entities.hand import Hand


class PlayerStrategy:
    def choose_action(
        self, hand: Hand, available_actions: list[Action], game_state: dict
    ) -> Action:
        raise NotImplementedError
