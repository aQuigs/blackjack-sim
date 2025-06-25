import random
from typing import Optional

from blackjack.entities.card import Card


class RandomWrapper:
    """
    Infrastructure wrapper for randomness. Delegates to an internal implementation.
    In live mode, uses random.shuffle. In null mode, shuffle is a no-op or uses a configured response.
    This is production code, not a test double.
    """

    class _LiveImpl:
        def shuffle(self, cards: list) -> None:
            random.shuffle(cards)

    class _NullImpl:
        def __init__(self, shuffle_response: Optional[list[Card]] = None) -> None:
            self._shuffle_response = shuffle_response

        def shuffle(self, cards: list[Card]) -> None:
            if self._shuffle_response:
                cards[:] = self._shuffle_response.copy()

    def __init__(self, null: bool = False, shuffle_response: Optional[list[Card]] = None) -> None:
        self._impl: "RandomWrapper._NullImpl | RandomWrapper._LiveImpl"
        if null:
            self._impl = self._NullImpl(shuffle_response)
        else:
            self._impl = self._LiveImpl()

    def shuffle(self, cards: list) -> None:
        self._impl.shuffle(cards)
