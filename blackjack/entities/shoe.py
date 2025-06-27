from typing import Optional

from blackjack.entities.card import Card
from blackjack.entities.deck_schema import DeckSchema
from blackjack.entities.random_wrapper import RandomWrapper


class Shoe:
    def __init__(
        self, deck_schema: DeckSchema, num_decks: int = 1, random_wrapper: Optional[RandomWrapper] = None
    ) -> None:
        self.cards: list[Card] = []
        self.dealt_cards: list[Card] = []
        self.randomizer = random_wrapper or RandomWrapper()

        card_counts = deck_schema.card_counts()
        for _ in range(num_decks):
            for (rank, suit), count in card_counts.items():
                for _ in range(count):
                    self.cards.append(Card(rank, suit))

        self.shuffle()

    @classmethod
    def create_null(cls, deck_schema: DeckSchema, num_decks: int = 1, cards: Optional[list[Card]] = None) -> "Shoe":
        return cls(deck_schema, num_decks, random_wrapper=RandomWrapper(null=True, shuffle_response=cards))

    def shuffle(self) -> None:
        self.cards.extend(self.dealt_cards)
        self.dealt_cards.clear()
        self.randomizer.shuffle(self.cards)

    def deal_card(self) -> Card:
        if not self.cards:
            raise ValueError("No more cards in the shoe.")

        card = self.cards.pop()
        self.dealt_cards.append(card)
        return card

    def cards_left(self) -> int:
        return len(self.cards)
