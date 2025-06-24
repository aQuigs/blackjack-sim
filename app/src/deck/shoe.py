import random
from app.src.deck.card import Card
from app.src.deck.deck_schema import DeckSchema


class Shoe:
    def __init__(self, deck_schema: DeckSchema, num_decks: int = 1):
        self.cards: list[Card] = []
        card_counts = deck_schema.card_counts()
        for _ in range(num_decks):
            for (rank, suit), count in card_counts.items():
                for _ in range(count):
                    self.cards.append(Card(rank, suit))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self) -> Card:
        if not self.cards:
            raise ValueError("No more cards in the shoe.")
        return self.cards.pop()

    def cards_left(self) -> int:
        return len(self.cards)
