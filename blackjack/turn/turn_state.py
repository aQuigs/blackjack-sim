from enum import Enum

from blackjack.gameplay.turn_handler import (
    PreDealHandler,
    CheckDealerAceHandler,
    CheckDealerBlackjackHandler,
    CheckPlayerBjWinHandler,
    CheckPlayerBjPushHandler,
    PlayerInitialTurnHandler,
    CheckPlayerCardStateHandler,
    PlayerTurnContinuedHandler,
    DealerTurnHandler,
    EvaluateGameHandler,
    GameOverHandler,
)


class TurnState(Enum):
    """Enum representing the different states of a turn in the game."""
    PRE_DEAL = PreDealHandler()
    CHECK_DEALER_ACE = CheckDealerAceHandler()
    CHECK_DEALER_BLACKJACK = CheckDealerBlackjackHandler()
    CHECK_PLAYER_BJ_WIN = CheckPlayerBjWinHandler()
    CHECK_PLAYER_BJ_PUSH = CheckPlayerBjPushHandler()
    PLAYER_INITIAL_TURN = PlayerInitialTurnHandler()
    CHECK_PLAYER_CARD_STATE = CheckPlayerCardStateHandler()
    PLAYER_TURN_CONTINUED = PlayerTurnContinuedHandler()
    DEALER_TURN = DealerTurnHandler()
    EVALUATE_GAME = EvaluateGameHandler()
    GAME_OVER_WIN = GameOverHandler()
    GAME_OVER_BJ = GameOverHandler()
    GAME_OVER_LOSE = GameOverHandler()
    GAME_OVER_PUSH = GameOverHandler()
    GAME_OVER_SURRENDER = GameOverHandler()
