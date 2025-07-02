from enum import Enum

from blackjack.entities.state import Turn
from blackjack.gameplay.turn_handler import (
    CheckDealerBjPossibleHandler,
    CheckDealerBlackjackHandler,
    CheckPlayerBjHandler,
    CheckPlayerCardStateHandler,
    DealAfterSplitHandler,
    EvaluateGameHandler,
    GameOverHandler,
    GameOverSplitHandler,
    NextSplitHandHandler,
    PreDealHandler,
    TakeTurnHandler,
)


class TurnState(Enum):
    PRE_DEAL = (PreDealHandler(), Turn.SETUP)
    CHECK_DEALER_BJ_POSSIBLE = (CheckDealerBjPossibleHandler(), Turn.SETUP)
    CHECK_DEALER_BLACKJACK = (CheckDealerBlackjackHandler(), Turn.SETUP)
    CHECK_PLAYER_BJ_WIN = (CheckPlayerBjHandler(), Turn.SETUP)
    CHECK_PLAYER_BJ_PUSH = (CheckPlayerBjHandler(), Turn.SETUP)
    DEAL_AFTER_SPLIT = (DealAfterSplitHandler(), Turn.SETUP)
    PLAYER_INITIAL_TURN = (TakeTurnHandler(is_player=True), Turn.PLAYER)
    CHECK_PLAYER_CARD_STATE = (CheckPlayerCardStateHandler(is_player=True), Turn.PLAYER)
    CHECK_PLAYER_CARD_STATE_END_TURN = (CheckPlayerCardStateHandler(is_player=True), Turn.INTERMEDIATE)
    PLAYER_TURN_CONTINUED = (TakeTurnHandler(is_player=True), Turn.PLAYER)
    NEXT_SPLIT_HAND = (NextSplitHandHandler(), Turn.INTERMEDIATE)
    DEALER_TURN = (TakeTurnHandler(is_player=False), Turn.DEALER)
    CHECK_DEALER_CARD_STATE = (CheckPlayerCardStateHandler(is_player=False), Turn.DEALER)
    EVALUATE_GAME = (EvaluateGameHandler(), Turn.FINALIZE)
    GAME_OVER_SPLIT = (GameOverSplitHandler(), Turn.FINALIZE)
    GAME_OVER_WIN = (GameOverHandler(), Turn.FINALIZE)
    GAME_OVER_BJ = (GameOverHandler(), Turn.FINALIZE)
    GAME_OVER_LOSE = (GameOverHandler(), Turn.FINALIZE)
    GAME_OVER_PUSH = (GameOverHandler(), Turn.FINALIZE)
    GAME_OVER_SURRENDER = (GameOverHandler(), Turn.FINALIZE)

    def __init__(self, handler, turn: Turn) -> None:
        self.handler = handler
        self.turn = turn
