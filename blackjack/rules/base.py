from typing import TYPE_CHECKING

from blackjack.entities.hand import Hand
from blackjack.entities.state import Outcome
from blackjack.turn.action import Action

if TYPE_CHECKING:
    from blackjack.turn.turn_state import TurnState  # pragma: nocover


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
        raise NotImplementedError  # pragma: nocover

    def is_blackjack(self, hand: Hand) -> bool:
        raise NotImplementedError  # pragma: nocover

    def is_bust(self, hand: Hand) -> bool:
        raise NotImplementedError  # pragma: nocover

    def dealer_should_hit(self, hand: Hand) -> bool:
        raise NotImplementedError  # pragma: nocover

    def blackjack_payout(self) -> float:
        raise NotImplementedError  # pragma: nocover

    def available_actions(self, turn_state: "TurnState") -> list[Action]:
        raise NotImplementedError  # pragma: nocover

    def get_outcome_payout(self, outcome: Outcome) -> float:
        raise NotImplementedError  # pragma: nocover

    def get_possible_outcomes(self) -> list[Outcome]:
        raise NotImplementedError  # pragma: nocover
