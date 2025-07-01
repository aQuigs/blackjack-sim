from blackjack.entities.card import Card
from blackjack.entities.hand import Hand
from blackjack.entities.state import Outcome
from blackjack.rules.base import HandValue, Rules
from blackjack.turn.action import Action
from blackjack.turn.turn_state import TurnState


class StandardBlackjackRules(Rules):
    def hand_value(self, hand: Hand) -> HandValue:
        value: int = 0
        aces: int = 0
        for card in hand.cards:
            if card.is_ten():
                value += 10
            elif card.rank == "A":
                aces += 1
                value += 11
            else:
                value += int(card.rank)
        while value > 21 and aces:
            value -= 10
            aces -= 1
        soft: bool = aces > 0 and value <= 21
        return HandValue(value, soft)

    def is_blackjack(self, hand: Hand) -> bool:
        hv: HandValue = self.hand_value(hand)
        return len(hand.cards) == 2 and hv.value == 21

    def is_bust(self, hand: Hand) -> bool:
        return self.hand_value(hand).value > 21

    def blackjack_payout(self) -> float:
        return 1.5

    def available_actions(self, turn_state: TurnState) -> list[Action]:
        if turn_state in [TurnState.PLAYER_INITIAL_TURN, TurnState.PLAYER_TURN_CONTINUED]:
            return [Action.HIT, Action.STAND]

        if turn_state == TurnState.DEALER_TURN:
            return [Action.HIT, Action.STAND]

        raise RuntimeError(f"Unexpected turn state to choose actions: {turn_state}")

    def translate_upcard(self, upcard: Card) -> str:
        return "10" if upcard.is_ten() else upcard.rank

    def get_outcome_payout(self, outcome: Outcome) -> float:
        if outcome == Outcome.BLACKJACK:
            return self.blackjack_payout()
        elif outcome == Outcome.WIN:
            return 1.0
        elif outcome == Outcome.LOSE:
            return -1.0
        elif outcome == Outcome.PUSH:
            return 0.0
        else:
            raise ValueError(f"Unknown outcome: {outcome}")

    def get_possible_outcomes(self) -> list[Outcome]:
        return [Outcome.WIN, Outcome.LOSE, Outcome.PUSH, Outcome.BLACKJACK]
