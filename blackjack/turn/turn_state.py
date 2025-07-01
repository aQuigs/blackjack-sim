from enum import Enum

from blackjack.entities.state import Turn
from blackjack.gameplay.turn_handler import (
    CheckDealerBjPossibleHandler,
    CheckDealerBlackjackHandler,
    CheckPlayerBjHandler,
    CheckPlayerCardStateHandler,
    EvaluateGameHandler,
    GameOverHandler,
    PreDealHandler,
    TakeTurnHandler,
)


class TurnState(Enum):
    PRE_DEAL = (PreDealHandler(), Turn.PLAYER)
    CHECK_DEALER_BJ_POSSIBLE = (CheckDealerBjPossibleHandler(), Turn.PLAYER)
    CHECK_DEALER_BLACKJACK = (CheckDealerBlackjackHandler(), Turn.PLAYER)
    CHECK_PLAYER_BJ_WIN = (CheckPlayerBjHandler(), Turn.PLAYER)
    CHECK_PLAYER_BJ_PUSH = (CheckPlayerBjHandler(), Turn.PLAYER)
    PLAYER_INITIAL_TURN = (TakeTurnHandler(is_player=True), Turn.PLAYER)
    CHECK_PLAYER_CARD_STATE = (CheckPlayerCardStateHandler(is_player=True), Turn.PLAYER)
    PLAYER_TURN_CONTINUED = (TakeTurnHandler(is_player=True), Turn.PLAYER)
    DEALER_TURN = (TakeTurnHandler(is_player=False), Turn.DEALER)
    CHECK_DEALER_CARD_STATE = (CheckPlayerCardStateHandler(is_player=False), Turn.DEALER)
    EVALUATE_GAME = (EvaluateGameHandler(), Turn.DEALER)
    GAME_OVER_WIN = (GameOverHandler(), Turn.PLAYER)
    GAME_OVER_BJ = (GameOverHandler(), Turn.PLAYER)
    GAME_OVER_LOSE = (GameOverHandler(), Turn.PLAYER)
    GAME_OVER_PUSH = (GameOverHandler(), Turn.PLAYER)
    GAME_OVER_SURRENDER = (GameOverHandler(), Turn.PLAYER)

    def __init__(self, handler, turn: Turn) -> None:
        self.handler = handler
        self.turn = turn
