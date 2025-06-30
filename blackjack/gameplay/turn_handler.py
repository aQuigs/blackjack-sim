from abc import ABC, abstractmethod
from enum import Enum, auto


class Decision(Enum):
    """Enum representing decisions made by turn handlers."""
    NEXT = auto()
    YES = auto()
    NO = auto()
    TAKE_CARD = auto()
    SURRENDER = auto()
    STAND = auto()
    BUST = auto()
    WINNER = auto()
    LOSER = auto()
    TIE = auto()


class TurnHandler(ABC):

    @abstractmethod
    def handle_turn(self, game_context) -> Decision, Action:
        pass

    def is_terminal(self) -> bool:
        """Return True if this handler represents a terminal state (game over)."""
        return False


class PreDealHandler(TurnHandler):
    """Handler for the pre-deal state of the game."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement pre-deal logic
        # This could include shuffling, placing bets, etc.
        return Decision.NEXT


class CheckDealerAceHandler(TurnHandler):
    """Handler for checking if dealer has an ace (insurance scenario)."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement dealer ace check logic
        # Check if dealer's up card is an ace and handle insurance
        return Decision.NEXT


class CheckDealerBlackjackHandler(TurnHandler):
    """Handler for checking if dealer has blackjack."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement dealer blackjack check logic
        # Check if dealer has blackjack after revealing hole card
        return Decision.NEXT


class CheckPlayerBjWinHandler(TurnHandler):
    """Handler for checking if player has blackjack and wins."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement player blackjack win check logic
        # Check if player has blackjack and dealer doesn't
        return Decision.NEXT


class CheckPlayerBjPushHandler(TurnHandler):
    """Handler for checking if player has blackjack and pushes."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement player blackjack push check logic
        # Check if both player and dealer have blackjack
        return Decision.NEXT


class PlayerInitialTurnHandler(TurnHandler):
    """Handler for the player's initial turn."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement player initial turn logic
        # Handle player's first action (hit, stand, double, split)
        return Decision.NEXT


class CheckPlayerCardStateHandler(TurnHandler):
    """Handler for checking the player's card state."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement player card state check logic
        # Check if player busted, has blackjack, or can continue
        return Decision.NEXT


class PlayerTurnContinuedHandler(TurnHandler):
    """Handler for continued player turns."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement continued player turn logic
        # Handle subsequent player actions after initial turn
        return Decision.NEXT


class DealerTurnHandler(TurnHandler):
    """Handler for the dealer's turn."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement dealer turn logic
        # Handle dealer's play according to house rules
        return Decision.NEXT


class EvaluateGameHandler(TurnHandler):
    """Handler for evaluating the final game state."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement game evaluation logic
        # Compare player and dealer hands to determine winner
        return Decision.NEXT


class GameOverHandler(TurnHandler):
    """Handler for the game over state."""

    def handle_turn(self, game_context) -> Decision:
        # TODO: Implement game over logic
        # Handle payout, reset game state, etc.
        return Decision.NEXT

    def is_terminal(self) -> bool:
        return True
