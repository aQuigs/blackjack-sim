from collections import defaultdict

from blackjack.entities.state import GraphState
from blackjack.turn.action import Action


def _default_next_state():
    return defaultdict(int)


def _default_action_transition():
    return defaultdict(_default_next_state)


class StateTransitionGraph:
    """
    Tracks transitions between states in a blackjack game.
    Structure: {state: {action: {next_state: count}}}
    """

    def __init__(self):
        self.transitions: dict[GraphState, dict[Action, dict[GraphState, int]]] = defaultdict(_default_action_transition)

    def add_transition(self, state: GraphState, action: Action, next_state: GraphState):
        self.transitions[state][action][next_state] += 1

    def get_graph(self) -> dict[GraphState, dict[Action, dict[GraphState, int]]]:
        return self.transitions

    def __repr__(self):
        return f"StateTransitionGraph(transitions={dict(self.transitions)})"

    def merge(self, other: "StateTransitionGraph") -> None:
        for state, actions in other.get_graph().items():
            for action, next_states in actions.items():
                for next_state, count in next_states.items():
                    self.transitions[state][action][next_state] += count
