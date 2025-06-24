from abc import ABC, abstractmethod
from typing import Dict, Tuple

from app.src.deck.card import Card


class DeckSchema(ABC):
    @abstractmethod
    def card_counts(self) -> Dict[Tuple[str, str], int]:
        """
        Returns a dictionary mapping (rank, suit) tuples to the number of cards of that type in the deck.
        Example: {('A', '♠'): 4, ('2', '♥'): 4, ...}
        """
        pass


class StandardBlackjackSchema(DeckSchema):
    def card_counts(self) -> Dict[Tuple[str, str], int]:
        return {(rank, suit): 1 for rank in Card.RANKS for suit in Card.SUITS}


class Spanish21Schema(DeckSchema):
    def card_counts(self) -> Dict[Tuple[str, str], int]:
        return {(rank, suit): 1 for rank in Card.RANKS if rank != '10' for suit in Card.SUITS}
