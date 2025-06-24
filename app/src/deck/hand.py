from app.src.deck.card import Card


class Hand:
    def __init__(self) -> None:
        self.cards: list[Card] = []

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    # Future: implement hand value, blackjack, bust, etc.