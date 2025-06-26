from collections import defaultdict

from blackjack.action import Action
from blackjack.entities.state import State


class StateTransitionGraph:
    """
    Tracks transitions between states in a blackjack game.
    Structure: {state: {action: {next_state: count}}}
    """

    def __init__(self):
        self.transitions: dict[State, dict[Action, dict[State, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )

    def add_transition(self, state: State, action: Action, next_state: State):
        self.transitions[state][action][next_state] += 1

    def get_graph(self) -> dict[State, dict[Action, dict[State, int]]]:
        return self.transitions

    def __repr__(self):
        return f"StateTransitionGraph(transitions={dict(self.transitions)})"
