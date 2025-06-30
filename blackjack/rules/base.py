from blackjack.entities.card import Card
from blackjack.entities.hand import Hand
from blackjack.entities.state import Outcome
from blackjack.turn.action import Action
from blackjack.turn.turn_state import TurnState


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

    def available_actions(self, turn_state: TurnState) -> list[Action]:
        raise NotImplementedError

    def determine_outcome(self, player_hand: Hand, dealer_hand: Hand):
        raise NotImplementedError

    def translate_upcard(self, upcard: Card):
        raise NotImplementedError

    def get_outcome_payout(self, outcome: Outcome) -> float:
        raise NotImplementedError

    def get_possible_outcomes(self) -> list[Outcome]:
        raise NotImplementedError
