from abc import ABC, abstractmethod
from typing import Dict, Tuple

from blackjack.entities.card import Card


class DeckSchema(ABC):
    @abstractmethod
    def card_counts(self) -> Dict[Tuple[str, str], int]:
        pass


class StandardBlackjackSchema(DeckSchema):
    def card_counts(self) -> Dict[Tuple[str, str], int]:
        return {(rank, suit): 1 for rank in Card.RANKS for suit in Card.SUITS}
