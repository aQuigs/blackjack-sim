from blackjack.entities.hand import Hand


class Player:
    def __init__(self, name: str):
        self.name = name
        self.hand = Hand()

    def __str__(self):
        return f"{self.name}: {self.hand}"

    def __repr__(self):
        return f"Player(name={self.name!r}, hand={self.hand!r})"

    # Future: add betting, strategy, etc.
