from blackjack.action import Action
from blackjack.entities.hand import Hand


class HandValue:
    def __init__(self, value: int, soft: bool) -> None:
        self.value: int = value
        self.soft: bool = soft

    def __repr__(self) -> str:
        return f"HandValue(value={self.value}, soft={self.soft})"

    def __str__(self) -> str:
        return f"{self.value}{', soft' if self.soft else ''}"


class Rules:
    def hand_value(self, hand: Hand) -> HandValue:
        raise NotImplementedError

    def is_blackjack(self, hand: Hand) -> bool:
        raise NotImplementedError

    def is_bust(self, hand: Hand) -> bool:
        raise NotImplementedError

    def dealer_should_hit(self, hand: Hand) -> bool:
        raise NotImplementedError

    def blackjack_payout(self) -> float:
        raise NotImplementedError

    def available_actions(self, hand: Hand, game_state: dict[str, object]) -> list[Action]:
        raise NotImplementedError

    def can_continue(self, hand: Hand, game_state: dict[str, object]) -> bool:
        raise NotImplementedError

    def determine_outcome(self, player_hand: Hand, dealer_hand: Hand):
        raise NotImplementedError
