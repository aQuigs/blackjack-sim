import logging
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable

from blackjack.entities.player import Player
from blackjack.entities.state import Outcome
from blackjack.game_events import (
    BlackjackEvent,
    BustEvent,
    ChooseActionEvent,
    DealEvent,
    DoubleEvent,
    GameEvent,
    HitEvent,
    TwentyOneEvent,
)
from blackjack.gameplay.game_context import GameContext
from blackjack.rules.base import HandValue, Rules
from blackjack.turn.action import Action

if TYPE_CHECKING:
    from blackjack.turn.turn_state import TurnState

logger = logging.getLogger(__name__)


class Decision(Enum):
    """Enum representing decisions made by turn handlers."""

    NEXT = auto()
    YES = auto()
    NO = auto()
    HIT = auto()
    SURRENDER = auto()
    DOUBLE = auto()
    STAND = auto()
    BUST = auto()
    WINNER = auto()
    LOSER = auto()
    TIE = auto()


class TurnHandler(ABC):

    @abstractmethod
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        pass

    def is_terminal(self) -> bool:
        return False

    def get_outcome(self, state: "TurnState") -> Outcome:
        from blackjack.turn.turn_state import TurnState

        OUTCOME_MAPPING = {
            TurnState.GAME_OVER_BJ: Outcome.BLACKJACK,
            TurnState.GAME_OVER_WIN: Outcome.WIN,
            TurnState.GAME_OVER_LOSE: Outcome.LOSE,
            TurnState.GAME_OVER_PUSH: Outcome.PUSH,
        }

        return OUTCOME_MAPPING.get(state, Outcome.IN_PROGRESS)


class PreDealHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        for _ in range(2):
            card = game_context.shoe.deal_card()
            game_context.player.hand.add_card(card)
            output_tracker(DealEvent(to=game_context.player.name, card=card))

            card = game_context.shoe.deal_card()
            game_context.dealer.hand.add_card(card)
            output_tracker(DealEvent(to=game_context.dealer.name, card=card))

        return Decision.NEXT, Action.NOOP


class CheckDealerBjPossibleHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        upcard = game_context.dealer.hand.cards[0]
        if upcard.is_ace() or upcard.is_ten():
            return Decision.YES, Action.NOOP
        else:
            return Decision.NO, Action.NOOP


class CheckDealerBlackjackHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        if game_context.rules.is_blackjack(game_context.dealer.hand):
            output_tracker(BlackjackEvent(player=game_context.dealer.name, hand=game_context.dealer.hand.cards.copy()))
            return Decision.YES, Action.NOOP
        else:
            return Decision.NO, Action.NOOP


class CheckPlayerBjHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        if game_context.rules.is_blackjack(game_context.player.hand):
            output_tracker(BlackjackEvent(player=game_context.player.name, hand=game_context.player.hand.cards.copy()))
            return Decision.YES, Action.NOOP
        else:
            return Decision.NO, Action.NOOP


class TakeTurnHandler(TurnHandler):
    def __init__(self, is_player: bool):
        super().__init__()
        self.is_player = is_player

    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        rules: Rules = game_context.rules
        actor: Player = game_context.player if self.is_player else game_context.dealer

        actions = rules.available_actions(state)
        if not actions:
            raise RuntimeError(
                f"No valid actions available for {actor.name} with hand {actor.hand.cards}. "
                f"Available actions: {actions}"
            )

        hand_value: HandValue = rules.hand_value(actor.hand)
        action: Action = actor.strategy.choose_action(actor.hand, actions, {})
        output_tracker(ChooseActionEvent(player=actor.name, action=action, hand=actor.hand.cards.copy()))
        if logger.isEnabledFor(logging.INFO):
            logging.info(f"{actor.name} chooses {action.name} with hand: {actor.hand} ({hand_value})")

        if action == Action.STAND:
            return Decision.STAND, (action if self.is_player else Action.NOOP)
        elif action == Action.HIT:
            card = game_context.shoe.deal_card()
            actor.hand.add_card(card)
            new_hand_value: HandValue = rules.hand_value(actor.hand)

            output_tracker(
                HitEvent(
                    player=actor.name,
                    card=card,
                    new_hand=actor.hand.cards.copy(),
                    value=new_hand_value.value,
                )
            )
            if logger.isEnabledFor(logging.INFO):
                logging.info(f"{actor.name} hit and receives: {card}. New hand: {actor.hand} ({new_hand_value})")

            return Decision.HIT, (action if self.is_player else Action.NOOP)
        elif action == Action.DOUBLE:
            card = game_context.shoe.deal_card()
            actor.hand.add_card(card)
            new_hand_value = rules.hand_value(actor.hand)

            output_tracker(
                DoubleEvent(
                    player=actor.name,
                    card=card,
                    new_hand=actor.hand.cards.copy(),
                    value=new_hand_value.value,
                )
            )
            if logger.isEnabledFor(logging.INFO):
                logging.info(f"{actor.name} doubles and receives: {card}. New hand: {actor.hand} ({new_hand_value})")

            return Decision.DOUBLE, (action if self.is_player else Action.NOOP)
        else:
            raise RuntimeError(
                f"Invalid action {action} for player {actor.name} with hand {actor.hand.cards}. "
                f"Available actions: {actions}"
            )


class CheckPlayerCardStateHandler(TurnHandler):
    def __init__(self, is_player: bool):
        super().__init__()
        self.is_player = is_player

    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        actor: Player = game_context.player if self.is_player else game_context.dealer

        rules: Rules = game_context.rules
        hand_value: HandValue = rules.hand_value(actor.hand)

        if rules.is_bust(actor.hand):
            output_tracker(BustEvent(player=actor.name, hand=actor.hand.cards.copy(), value=hand_value.value))
            if logger.isEnabledFor(logging.INFO):
                logging.info(f"{actor.name} busts with hand: {actor.hand} ({hand_value})")
            return Decision.BUST, Action.NOOP

        if hand_value.value == 21:
            output_tracker(TwentyOneEvent(player=actor.name, hand=actor.hand.cards.copy()))
            return Decision.STAND, Action.NOOP

        return Decision.NEXT, Action.NOOP


class EvaluateGameHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        player_value: int = game_context.rules.hand_value(game_context.player.hand).value
        dealer_value: int = game_context.rules.hand_value(game_context.dealer.hand).value

        if player_value > dealer_value:
            return Decision.WINNER, Action.NOOP
        elif player_value < dealer_value:
            return Decision.LOSER, Action.NOOP
        else:
            return Decision.TIE, Action.NOOP


class GameOverHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        raise NotImplementedError

    def is_terminal(self) -> bool:
        return True
