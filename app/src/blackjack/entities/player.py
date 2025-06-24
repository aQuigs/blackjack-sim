from app.src.blackjack.entities.hand import Hand


class Player:
    def __init__(self, name: str):
        self.name = name
        self.hand = Hand()

    # Future: add betting, strategy, etc.
