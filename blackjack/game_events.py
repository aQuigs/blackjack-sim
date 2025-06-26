from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

from blackjack.action import Action
from blackjack.entities.card import Card
from blackjack.entities.state_transition_graph import StateTransitionGraph


class GameEventType(Enum):
    DEAL = auto()
    BUST = auto()
    BLACKJACK = auto()
    TWENTY_ONE = auto()
    NO_ACTIONS = auto()
    CHOOSE_ACTION = auto()
    HIT = auto()
    INVALID_ACTION = auto()


class PlayerOutcome(Enum):
    BUST = auto()
    BLACKJACK = auto()
    ACTIVE = auto()


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
    outcome: PlayerOutcome


@dataclass(frozen=True)
class GameResult:
    player_results: list[PlayerResult]
    dealer_hand: list[Card]
    winner: Optional[Winner]
    state_transition_graph: StateTransitionGraph


@dataclass(frozen=True)
class GameEvent:
    type: GameEventType
    payload: Any
