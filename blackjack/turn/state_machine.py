from blackjack.gameplay.turn_handler import Decision
from blackjack.turn.turn_state import TurnState


class InvalidTransition(Exception):
    """Raised when no valid transition is defined for a state and decision combination."""

    def __init__(self, current_state: TurnState, decision: Decision):
        self.decision = decision
        super().__init__(f"No transition defined for {current_state} with decision {decision}")


class StateMachine:
    def __init__(self, machine: dict[TurnState, dict[Decision, TurnState]]) -> None:
        self.machine = machine

    def transition(self, current_state: TurnState, decision: Decision) -> TurnState:
        """Transition to the next state based on the current state and decision."""
        if current_state in self.machine and decision in self.machine[current_state]:
            self.state = self.machine[current_state][decision]
        else:
            raise InvalidTransition(current_state, decision)

        return self.state
