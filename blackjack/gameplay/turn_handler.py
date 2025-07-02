import logging
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable

from blackjack.entities.hand import Hand
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
    SPLIT = auto()
    STAND = auto()
    BUST = auto()
    WINNER = auto()
    LOSER = auto()
    TIE = auto()
    MIX = auto()


class TurnHandler(ABC):

    @abstractmethod
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        pass

    def is_terminal(self) -> bool:
        return False

    def get_outcomes(self, game_context: GameContext, state: "TurnState") -> list[Outcome]:
        from blackjack.turn.turn_state import TurnState

        OUTCOME_MAPPING = {
            TurnState.GAME_OVER_BJ: Outcome.BLACKJACK,
            TurnState.GAME_OVER_WIN: Outcome.WIN,
            TurnState.GAME_OVER_LOSE: Outcome.LOSE,
            TurnState.GAME_OVER_PUSH: Outcome.PUSH,
        }

        return [OUTCOME_MAPPING.get(state, Outcome.IN_PROGRESS)]


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


class DealAfterSplitHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        if not game_context.has_split():
            raise RuntimeError("DealAfterSplitHandler called without a split in progress")

        while len(game_context.player.hand.cards) < 2:
            card = game_context.shoe.deal_card()
            game_context.player.hand.add_card(card)
            output_tracker(DealEvent(to=game_context.player.name, card=card))

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
    def __init__(self, is_split: bool):
        super().__init__()
        self.is_split = is_split

    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        if game_context.rules.is_blackjack(game_context.player.hand):
            if self.is_split:
                output_tracker(
                    TwentyOneEvent(player=game_context.player.name, hand=game_context.player.hand.cards.copy())
                )
            else:
                output_tracker(
                    BlackjackEvent(player=game_context.player.name, hand=game_context.player.hand.cards.copy())
                )
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

        # Skip dealer's turn if all players are busted
        if not self.is_player and all(rules.is_bust(hand) for hand in game_context.player.hands):
            return Decision.STAND, Action.NOOP

        actions = rules.available_actions(state, actor.hand.is_pair(), len(actor.hands) - 1)
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
        elif action == Action.SPLIT:
            if not actor.hand.is_pair():
                raise RuntimeError(f"Cannot split hand {actor.hand.cards} as it is not a pair.")

            actor.split_active_hand()
            return Decision.SPLIT, Action.SPLIT
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


class NextSplitHandHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        game_context.player.active_index += 1
        if game_context.player.active_index < len(game_context.player.hands):
            return Decision.YES, Action.NOOP
        else:
            # Reset for easy evaluation
            game_context.player.active_index = 0
            return Decision.NO, Action.NOOP


def determine_hand_outcome(rules: Rules, player_hand: Hand, dealer_hand: Hand) -> Outcome:
    player_value: int = rules.hand_value(player_hand).value
    dealer_value: int = rules.hand_value(dealer_hand).value

    if rules.is_bust(player_hand):
        return Outcome.LOSE
    elif rules.is_bust(dealer_hand):
        return Outcome.WIN
    elif player_value > dealer_value:
        return Outcome.WIN
    elif player_value < dealer_value:
        return Outcome.LOSE
    else:
        return Outcome.PUSH


class EvaluateGameHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        if game_context.has_split():
            return Decision.MIX, Action.NOOP

        rules: Rules = game_context.rules
        player: Player = game_context.player
        dealer: Player = game_context.dealer

        outcome: Outcome = determine_hand_outcome(rules, player.hand, dealer.hand)

        if outcome == Outcome.WIN:
            return Decision.WINNER, Action.NOOP
        elif outcome == Outcome.LOSE:
            return Decision.LOSER, Action.NOOP
        elif outcome == Outcome.PUSH:
            return Decision.TIE, Action.NOOP
        else:
            raise RuntimeError(
                f"Unexpected outcome {outcome} for player hand {player.hand.cards} and dealer hand {dealer.hand.cards}"
            )


class GameOverHandler(TurnHandler):
    def handle_turn(
        self, state: "TurnState", game_context: GameContext, output_tracker: Callable[[GameEvent], None]
    ) -> tuple[Decision, Action]:
        raise NotImplementedError

    def is_terminal(self) -> bool:
        return True


class GameOverSplitHandler(GameOverHandler):
    def get_outcomes(self, game_context: GameContext, state: "TurnState") -> list[Outcome]:
        rules: Rules = game_context.rules
        player: Player = game_context.player
        dealer: Player = game_context.dealer

        return [determine_hand_outcome(rules, hand, dealer.hand) for hand in player.hands]
