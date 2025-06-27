from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar, Optional, Union

from blackjack.action import Action
from blackjack.entities.card import Card
from blackjack.entities.state import Outcome


class GameEventType(Enum):
    DEAL = auto()
    BUST = auto()
    BLACKJACK = auto()
    TWENTY_ONE = auto()
    CHOOSE_ACTION = auto()
    HIT = auto()
    ROUND_RESULT = auto()


@dataclass(frozen=True)
class DealEvent:
    event_type: ClassVar[GameEventType] = GameEventType.DEAL
    to: str
    card: Card


@dataclass(frozen=True)
class BustEvent:
    event_type: ClassVar[GameEventType] = GameEventType.BUST
    player: str
    hand: list[Card]
    value: int


@dataclass(frozen=True)
class BlackjackEvent:
    event_type: ClassVar[GameEventType] = GameEventType.BLACKJACK
    player: str
    hand: list[Card]


@dataclass(frozen=True)
class TwentyOneEvent:
    event_type: ClassVar[GameEventType] = GameEventType.TWENTY_ONE
    player: str
    hand: list[Card]


@dataclass(frozen=True)
class ChooseActionEvent:
    event_type: ClassVar[GameEventType] = GameEventType.CHOOSE_ACTION
    player: str
    action: Action
    hand: list[Card]


@dataclass(frozen=True)
class HitEvent:
    event_type: ClassVar[GameEventType] = GameEventType.HIT
    player: str
    card: Card
    new_hand: list[Card]
    value: int


@dataclass(frozen=True)
class PlayerResult:
    name: str
    hand: list[Card]
    outcome: Outcome


@dataclass(frozen=True)
class RoundResultEvent:
    event_type: ClassVar[GameEventType] = GameEventType.ROUND_RESULT
    name: str
    hand: list[Card]
    outcome: Optional[Outcome] = None  # Dealer will have outcome=None


GameEvent = Union[
    DealEvent,
    BustEvent,
    BlackjackEvent,
    TwentyOneEvent,
    ChooseActionEvent,
    HitEvent,
    RoundResultEvent,
]
