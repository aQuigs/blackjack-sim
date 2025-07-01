from blackjack.gameplay.turn_handler import Decision
from blackjack.turn.state_machine import StateMachine
from blackjack.turn.turn_state import TurnState


def blackjack_state_machine():
    return StateMachine(
        {
            TurnState.PRE_DEAL: {
                Decision.NEXT: TurnState.CHECK_DEALER_BJ_POSSIBLE,
            },
            TurnState.CHECK_DEALER_BJ_POSSIBLE: {
                Decision.YES: TurnState.CHECK_DEALER_BLACKJACK,
                Decision.NO: TurnState.CHECK_PLAYER_BJ_WIN,
            },
            TurnState.CHECK_DEALER_BLACKJACK: {
                Decision.YES: TurnState.CHECK_PLAYER_BJ_PUSH,
                Decision.NO: TurnState.CHECK_PLAYER_BJ_WIN,
            },
            TurnState.CHECK_PLAYER_BJ_WIN: {
                Decision.YES: TurnState.GAME_OVER_BJ,
                Decision.NO: TurnState.PLAYER_INITIAL_TURN,
            },
            TurnState.CHECK_PLAYER_BJ_PUSH: {
                Decision.YES: TurnState.GAME_OVER_PUSH,
                Decision.NO: TurnState.GAME_OVER_LOSE,
            },
            TurnState.PLAYER_INITIAL_TURN: {
                Decision.TAKE_CARD: TurnState.CHECK_PLAYER_CARD_STATE,
                Decision.SURRENDER: TurnState.GAME_OVER_SURRENDER,
                Decision.STAND: TurnState.DEALER_TURN,
            },
            TurnState.CHECK_PLAYER_CARD_STATE: {
                Decision.NEXT: TurnState.PLAYER_TURN_CONTINUED,
                Decision.BUST: TurnState.GAME_OVER_LOSE,
                Decision.STAND: TurnState.DEALER_TURN,
            },
            TurnState.PLAYER_TURN_CONTINUED: {
                Decision.TAKE_CARD: TurnState.CHECK_PLAYER_CARD_STATE,
                Decision.STAND: TurnState.DEALER_TURN,
            },
            TurnState.DEALER_TURN: {
                Decision.STAND: TurnState.EVALUATE_GAME,
                Decision.TAKE_CARD: TurnState.CHECK_DEALER_CARD_STATE,
            },
            TurnState.CHECK_DEALER_CARD_STATE: {
                Decision.NEXT: TurnState.DEALER_TURN,
                Decision.BUST: TurnState.GAME_OVER_WIN,
                Decision.STAND: TurnState.EVALUATE_GAME,
            },
            TurnState.EVALUATE_GAME: {
                Decision.WINNER: TurnState.GAME_OVER_WIN,
                Decision.LOSER: TurnState.GAME_OVER_LOSE,
                Decision.TIE: TurnState.GAME_OVER_PUSH,
            },
        },
    )
