import random
from typing import Any, Optional, TypeVar

from blackjack.entities.card import Card

T = TypeVar("T")


class RandomWrapper:
    class _LiveImpl:
        def shuffle(self, cards: list) -> None:
            random.shuffle(cards)

        def choice(self, items: list[T]) -> T:
            return random.choice(items)

    class _NullImpl:
        def __init__(
            self, shuffle_response: Optional[list[Card]] = None, choice_responses: Optional[list[Any]] = None
        ) -> None:
            self._shuffle_response = shuffle_response
            self._choice_responses = choice_responses or []

        def shuffle(self, cards: list[Card]) -> None:
            if self._shuffle_response:
                cards[:] = self._shuffle_response.copy()

        def choice(self, items: list[T]) -> T:
            if not self._choice_responses:
                return items[0]

            response = self._choice_responses.pop(0)
            if response not in items:
                raise ValueError(f"Configured choice response {response} not in available items {items}")

            return response

    def __init__(
        self,
        null: bool = False,
        shuffle_response: Optional[list[Card]] = None,
        choice_responses: Optional[list[Any]] = None,
    ) -> None:
        self._impl: "RandomWrapper._NullImpl | RandomWrapper._LiveImpl"
        if null:
            self._impl = self._NullImpl(shuffle_response, choice_responses)
        else:
            self._impl = self._LiveImpl()

    def shuffle(self, cards: list) -> None:
        self._impl.shuffle(cards)

    def choice(self, items: list[T]) -> T:
        return self._impl.choice(items)
