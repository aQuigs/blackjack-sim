from app.src.blackjack.rules.base import HandValue, Rules
from app.src.blackjack.entities.hand import Hand
from app.src.blackjack.game import Action


class StandardBlackjackRules(Rules):
    def hand_value(self, hand: Hand) -> HandValue:
        value = 0
        aces = 0
        for card in hand.cards:
            if card.rank in {'J', 'Q', 'K'}:
                value += 10
            elif card.rank == 'A':
                aces += 1
                value += 11
            else:
                value += int(card.rank)
        while value > 21 and aces:
            value -= 10
            aces -= 1
        soft = aces > 0 and value <= 21
        return HandValue(value, soft)

    def is_blackjack(self, hand: Hand) -> bool:
        hv = self.hand_value(hand)
        return len(hand.cards) == 2 and hv.value == 21

    def is_bust(self, hand: Hand) -> bool:
        return self.hand_value(hand).value > 21

    def dealer_should_hit(self, hand: Hand) -> bool:
        hv = self.hand_value(hand)
        return hv.value < 17 or (hv.value == 17 and hv.soft)

    def blackjack_payout(self) -> float:
        return 1.5

    def available_actions(self, hand: Hand, game_state: dict) -> list[Action]:
        if self.is_bust(hand):
            return []
        return [Action.HIT, Action.STAND]

    def can_continue(self, hand: Hand, game_state: dict) -> bool:
        return not self.is_bust(hand)
