from dataclasses import dataclass
from enum import Enum, auto


class Turn(Enum):
    PLAYER = auto()
    DEALER = auto()
    SETUP = auto()
    FINALIZE = auto()
    INTERMEDIATE = auto()


class Outcome(Enum):
    WIN = auto()
    LOSE = auto()
    PUSH = auto()
    BLACKJACK = auto()
    IN_PROGRESS = auto()


class GraphState:
    """
    Base class for all graph state types in blackjack.
    """

    pass


@dataclass(frozen=True)
class ProperState(GraphState):
    """
    Represents a unique decision point in a blackjack game (not terminal).
    Extensible for splits, doubles, true count, etc.
    """

    player_hand_value: int
    player_hand_soft: bool
    dealer_upcard_rank: str
    turn: Turn
    split_count: int


@dataclass(frozen=True)
class PairState(GraphState):
    """
    Represents a state where the player has a pair (e.g., after being dealt 8-8)
    """

    pair_rank: str
    turn: Turn
    dealer_upcard: str
    split_count: int


@dataclass(frozen=True)
class TerminalState(GraphState):
    """
    Represents a terminal state (win/lose/push/bust/blackjack) in a blackjack game.
    """

    outcome: Outcome


@dataclass(frozen=True)
class PendingSplitHandState(GraphState):
    player_card: str
    dealer_upcard_rank: str
    min_split_count: int


@dataclass(frozen=True)
class NewSplitHandState(GraphState):
    player_card: str
    dealer_upcard_rank: str
    split_count: int


@dataclass(frozen=True)
class PreDealState(GraphState):
    """
    Represents the state before any cards are dealt.
    """

    pass


@dataclass(frozen=True)
class CompoundState(GraphState):
    """
    Represents a state where the player has split and has multiple hands, each represented as a GraphState.
    """

    active_index: int
    hand_states: tuple[GraphState, ...]
    dealer_upcard_rank: str
    turn: Turn


@dataclass(frozen=True)
class SplitState(GraphState):
    first_hand_state: NewSplitHandState
    second_hand_state: PendingSplitHandState
