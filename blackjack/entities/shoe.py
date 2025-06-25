import random
from typing import List, Optional, Callable

from blackjack.entities.card import Card
from blackjack.entities.deck_schema import DeckSchema


class ShuffleWrapper:
    """
    Infrastructure wrapper for shuffling. In live mode, uses random.shuffle.
    In null mode, shuffle is a no-op unless a configured response is provided.
    This is production code, not a test double.
    """
    def __init__(self, null: bool = False, shuffle_response: Optional[Callable[[List[Card]], None]] = None):
        self.null = null
        self.shuffle_response = shuffle_response

    def shuffle(self, cards: List[Card]) -> None:
        if self.null:
            if self.shuffle_response:
                self.shuffle_response(cards)
            # else: no-op
        else:
            random.shuffle(cards)


class Shoe:
    """
    Represents a shoe of cards for blackjack. Supports a null mode for tests, admin tools, or simulations.
    In null mode, shuffle() uses a no-op or a configured response instead of random.shuffle.
    This is production code, not a test double.
    """
    def __init__(self, deck_schema: Optional[DeckSchema], num_decks: int = 1, *, _cards: Optional[List[Card]] = None, _shuffler: Optional[ShuffleWrapper] = None) -> None:
        self._shuffler = _shuffler or ShuffleWrapper()
        self.cards: list[Card] = []
        if _cards is not None:
            # Null mode: use the provided card order
            self.cards = _cards.copy()
            self._null = True
        else:
            if deck_schema is None:
                raise ValueError("deck_schema must not be None unless using null mode")
            card_counts = deck_schema.card_counts()
            for _ in range(num_decks):
                for (rank, suit), count in card_counts.items():
                    for _ in range(count):
                        self.cards.append(Card(rank, suit))
            self._null = False
            self.shuffle()

    def shuffle(self) -> None:
        self._shuffler.shuffle(self.cards)

    def deal_card(self) -> Card:
        if not self.cards:
            raise ValueError("No more cards in the shoe.")
        return self.cards.pop()

    def cards_left(self) -> int:
        return len(self.cards)

    @classmethod
    def createNull(cls, cards: List[Card], shuffle_response: Optional[Callable[[List[Card]], None]] = None) -> "Shoe":
        """
        Create a null shoe with a configured card order and a ShuffleWrapper in null mode.
        shuffle_response, if provided, will be used instead of a no-op for shuffle().
        This is production code, not a test double. Useful for tests, admin tools, or simulations.
        """
        return cls(
            deck_schema=None,
            num_decks=1,
            _cards=cards,
            _shuffler=ShuffleWrapper(null=True, shuffle_response=shuffle_response),
        )
