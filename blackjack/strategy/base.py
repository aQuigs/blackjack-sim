from blackjack.entities.hand import Hand
from blackjack.turn.action import Action


class Strategy:
    def choose_action(self, hand: Hand, available_actions: list[Action], game_state: dict[str, object]) -> Action:
        raise NotImplementedError  # pragma: nocover
