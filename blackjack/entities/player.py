from blackjack.entities.hand import Hand
from blackjack.strategy.base import Strategy


class Player:
    def __init__(self, name: str, strategy: Strategy):
        if strategy is None:
            raise ValueError("Strategy cannot be None")
        self.name = name
        self.hand = Hand()
        self.strategy = strategy

    def __str__(self):
        return f"{self.name}: {self.hand}"

    def __repr__(self):
        return f"Player(name={self.name!r}, hand={self.hand!r})"
