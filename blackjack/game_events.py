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
    NO_ACTIONS = auto()
    CHOOSE_ACTION = auto()
    HIT = auto()
    INVALID_ACTION = auto()
    ROUND_RESULT = auto()


class Winner(Enum):
    DEALER = auto()
    PLAYER = auto()
    PUSH = auto()
    NONE = auto()


@dataclass(frozen=True)
class DealEvent:
    to: str
    card: str


@dataclass(frozen=True)
class BustEvent:
    player: str
    hand: str
    value: int


@dataclass(frozen=True)
class BlackjackEvent:
    player: str
    hand: str
    value: int


@dataclass(frozen=True)
class TwentyOneEvent:
    player: str
    hand: str


@dataclass(frozen=True)
class NoActionsEvent:
    player: str
    hand: str


@dataclass(frozen=True)
class ChooseActionEvent:
    player: str
    action: Action
    hand: str


@dataclass(frozen=True)
class HitEvent:
    player: str
    card: str
    new_hand: str
    value: int


@dataclass(frozen=True)
class InvalidActionEvent:
    player: str
    action: str
    hand: str


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
    winner: Optional[Winner] = None  # Only set for single-player games
