from blackjack.entities.card import Card


class Hand:
    def __init__(self) -> None:
        self.cards: list[Card] = []

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    def is_pair(self) -> bool:
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank

    def __str__(self) -> str:
        return "[" + ", ".join(str(card) for card in self.cards) + "]"

    def __repr__(self) -> str:
        return f"Hand({self.cards!r})"
