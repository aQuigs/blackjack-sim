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
            TurnState.DEAL_AFTER_SPLIT: {
                Decision.NEXT: TurnState.PLAYER_INITIAL_TURN,
            },
            TurnState.PLAYER_INITIAL_TURN: {
                Decision.HIT: TurnState.CHECK_PLAYER_CARD_STATE,
                Decision.SURRENDER: TurnState.GAME_OVER_SURRENDER,
                Decision.DOUBLE: TurnState.CHECK_PLAYER_CARD_STATE_END_TURN,
                Decision.SPLIT: TurnState.DEAL_AFTER_SPLIT,
                Decision.STAND: TurnState.NEXT_SPLIT_HAND,
            },
            TurnState.CHECK_PLAYER_CARD_STATE: {
                Decision.NEXT: TurnState.PLAYER_TURN_CONTINUED,
                Decision.BUST: TurnState.NEXT_SPLIT_HAND,
                Decision.STAND: TurnState.NEXT_SPLIT_HAND,
            },
            TurnState.CHECK_PLAYER_CARD_STATE_END_TURN: {
                Decision.BUST: TurnState.NEXT_SPLIT_HAND,
                Decision.NEXT: TurnState.NEXT_SPLIT_HAND,
                Decision.STAND: TurnState.NEXT_SPLIT_HAND,
            },
            TurnState.PLAYER_TURN_CONTINUED: {
                Decision.HIT: TurnState.CHECK_PLAYER_CARD_STATE,
                Decision.STAND: TurnState.NEXT_SPLIT_HAND,
            },
            TurnState.NEXT_SPLIT_HAND: {
                Decision.YES: TurnState.DEAL_AFTER_SPLIT,
                Decision.NO: TurnState.DEALER_TURN,
            },
            TurnState.DEALER_TURN: {
                Decision.STAND: TurnState.EVALUATE_GAME,
                Decision.HIT: TurnState.CHECK_DEALER_CARD_STATE,
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
                Decision.MIX: TurnState.GAME_OVER_SPLIT,
            },
        },
    )
