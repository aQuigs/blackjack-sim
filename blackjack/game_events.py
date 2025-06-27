from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

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
    to: str
    card: Card


@dataclass(frozen=True)
class BustEvent:
    player: str
    hand: list[Card]
    value: int


@dataclass(frozen=True)
class BlackjackEvent:
    player: str
    hand: list[Card]


@dataclass(frozen=True)
class TwentyOneEvent:
    player: str
    hand: list[Card]


@dataclass(frozen=True)
class ChooseActionEvent:
    player: str
    action: Action
    hand: list[Card]


@dataclass(frozen=True)
class HitEvent:
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
class GameEvent:
    type: GameEventType
    payload: Any


@dataclass(frozen=True)
class RoundResultEvent:
    name: str
    hand: list[Card]
    outcome: Optional[Outcome] = None  # Dealer will have outcome=None
