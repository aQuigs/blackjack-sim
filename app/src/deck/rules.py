from app.src.deck.hand import Hand
from app.src.deck.game import Action


class HandValue:
    def __init__(self, value: int, soft: bool):
        self.value = value
        self.soft = soft

    def __repr__(self):
        return f"HandValue(value={self.value}, soft={self.soft})"


class Rules:
    def hand_value(self, hand: Hand) -> HandValue:
        """Calculate the value of a hand according to the rules."""
        raise NotImplementedError

    def is_blackjack(self, hand: Hand) -> bool:
        """Determine if the hand is a blackjack."""
        raise NotImplementedError

    def is_bust(self, hand: Hand) -> bool:
        """Determine if the hand is bust."""
        raise NotImplementedError

    def dealer_should_hit(self, hand: Hand) -> bool:
        """Determine if the dealer should hit according to the rules."""
        raise NotImplementedError

    def blackjack_payout(self) -> float:
        """Return the payout multiplier for blackjack."""
        raise NotImplementedError

    def available_actions(self, hand: Hand, game_state: dict) -> list[Action]:
        """Return a list of actions available to the player for the given hand and game state."""
        raise NotImplementedError

    def can_continue(self, hand: Hand, game_state: dict) -> bool:
        """Return True if the player can continue acting on this hand."""
        raise NotImplementedError

    # Add more rule methods as needed for different game styles


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