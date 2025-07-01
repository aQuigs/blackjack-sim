from blackjack.entities.hand import Hand
from blackjack.strategy.base import Strategy


class Player:
    def __init__(self, name: str, strategy: Strategy) -> None:
        self.name: str = name
        self.hands: list[Hand] = [Hand()]
        self.active_index: int = 0
        self.strategy: Strategy = strategy

    @property
    def hand(self) -> Hand:
        return self.hands[self.active_index]

    def split_active_hand(self) -> None:
        if len(self.hand.cards) != 2:
            raise RuntimeError(f"Cannot split a hand that does not have exactly two cards: {self.hand!r}")

        new_hand = Hand()
        new_hand.add_card(self.hand.cards.pop())
        self.hands.insert(self.active_index + 1, new_hand)

    def __str__(self) -> str:
        return f"{self.name}: {self.hands}"

    def __repr__(self) -> str:
        return f"Player(name={self.name!r}, hand={self.hands!r}, active_index={self.active_index!r})"
