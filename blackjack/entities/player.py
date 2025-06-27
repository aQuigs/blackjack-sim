from blackjack.entities.hand import Hand
from blackjack.strategy.base import Strategy


class Player:
    def __init__(self, name: str, strategy: Strategy) -> None:
        self.name: str = name
        self.hand: Hand = Hand()
        self.strategy: Strategy = strategy

    def __str__(self) -> str:
        return f"{self.name}: {self.hand}"

    def __repr__(self) -> str:
        return f"Player(name={self.name!r}, hand={self.hand!r})"
