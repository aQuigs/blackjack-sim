from enum import Enum, auto
from typing import Union


class Turn(Enum):
    PLAYER = auto()
    DEALER = auto()


class Outcome(Enum):
    WIN = auto()
    LOSE = auto()
    PUSH = auto()
    BLACKJACK = auto()
    IN_PROGRESS = auto()


class GameState:
    """
    Base class for all state types in blackjack.
    """

    pass


class ProperState(GameState):
    """
    Represents a unique decision point in a blackjack game (not terminal).
    Extensible for splits, doubles, true count, etc.
    """

    def __init__(
        self,
        player_hand_value: int,
        player_hand_soft: bool,
        dealer_upcard_rank: str,
        turn: Turn,
    ):
        self.player_hand_value = player_hand_value
        self.player_hand_soft = player_hand_soft
        self.dealer_upcard_rank = dealer_upcard_rank
        self.turn = turn

    def __eq__(self, other):
        if not isinstance(other, ProperState):
            return NotImplemented

        return (
            self.player_hand_value == other.player_hand_value
            and self.player_hand_soft == other.player_hand_soft
            and self.dealer_upcard_rank == other.dealer_upcard_rank
            and self.turn == other.turn
        )

    def __hash__(self):
        return hash((self.player_hand_value, self.player_hand_soft, self.dealer_upcard_rank, self.turn))

    def __repr__(self):
        return (
            f"ProperState(player_hand_value={self.player_hand_value}, "
            f"player_hand_soft={self.player_hand_soft}, "
            f"dealer_upcard_rank='{self.dealer_upcard_rank}', "
            f"turn={self.turn})"
        )


class TerminalState(GameState):
    """
    Represents a terminal state (win/lose/push/bust/blackjack) in a blackjack game.
    """

    def __init__(self, outcome: Outcome):
        assert outcome in (Outcome.WIN, Outcome.LOSE, Outcome.PUSH, Outcome.BUST, Outcome.BLACKJACK)
        self.outcome = outcome

    def __eq__(self, other):
        if not isinstance(other, TerminalState):
            return NotImplemented
        return self.outcome == other.outcome

    def __hash__(self):
        return hash(self.outcome)

    def __repr__(self):
        return f"TerminalState(outcome={self.outcome})"


class PreDealState(GameState):
    """
    Represents the state before any cards are dealt.
    """

    def __eq__(self, other):
        if not isinstance(other, PreDealState):
            return NotImplemented

        return True

    def __hash__(self):
        return hash("PreDealState")

    def __repr__(self):
        return "PreDealState()"


State = Union[PreDealState, ProperState, TerminalState]
