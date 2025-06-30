from enum import Enum

from blackjack.gameplay.turn_handler import (
    CheckDealerAceHandler,
    CheckDealerBlackjackHandler,
    CheckPlayerBjHandler,
    CheckPlayerCardStateHandler,
    EvaluateGameHandler,
    GameOverHandler,
    PreDealHandler,
    TakeTurnHandler,
)


class TurnState(Enum):
    PRE_DEAL = PreDealHandler()
    CHECK_DEALER_ACE = CheckDealerAceHandler()
    CHECK_DEALER_BLACKJACK = CheckDealerBlackjackHandler()
    CHECK_PLAYER_BJ_WIN = CheckPlayerBjHandler()
    CHECK_PLAYER_BJ_PUSH = CheckPlayerBjHandler()
    PLAYER_INITIAL_TURN = TakeTurnHandler(is_player=True)
    CHECK_PLAYER_CARD_STATE = CheckPlayerCardStateHandler(is_player=True)
    PLAYER_TURN_CONTINUED = TakeTurnHandler(is_player=True)
    DEALER_TURN = TakeTurnHandler(is_player=False)
    CHECK_DEALER_CARD_STATE = CheckPlayerCardStateHandler(is_player=False)
    EVALUATE_GAME = EvaluateGameHandler()
    GAME_OVER_WIN = GameOverHandler()
    GAME_OVER_BJ = GameOverHandler()
    GAME_OVER_LOSE = GameOverHandler()
    GAME_OVER_PUSH = GameOverHandler()
    GAME_OVER_SURRENDER = GameOverHandler()
