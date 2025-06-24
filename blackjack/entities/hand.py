from blackjack.entities.card import Card


class Hand:
    def __init__(self) -> None:
        self.cards: list[Card] = []

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def __str__(self):
        return "[" + ", ".join(str(card) for card in self.cards) + "]"

    def __repr__(self):
        return f"Hand({self.cards!r})"
