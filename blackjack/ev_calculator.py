from dataclasses import dataclass
from graphlib import TopologicalSorter

from blackjack.action import Action
from blackjack.entities.state import State, TerminalState
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.rules.base import Rules


@dataclass
class StateEV:
    optimal_action: Action
    action_evs: dict[Action, float]


class EVCalculator:
    def __init__(self, rules: Rules):
        self.rules = rules

    def calculate_evs(self, graph: StateTransitionGraph) -> dict[State, StateEV]:
        transitions = graph.get_graph()

        if not transitions:
            return {}

        state_evs: dict[State, StateEV] = {}

        self._initialize_terminal_states(transitions, state_evs)
        sorted_states = self._topological_sort(transitions)

        for state in reversed(sorted_states):
            if isinstance(state, TerminalState):
                continue

            if state not in transitions:
                raise ValueError(f"State {state} is in the graph but not in transitions. This is a bug.")

            action_evs = self._calculate_action_evs(state, transitions[state], state_evs)

            optimal_action = max(action_evs, key=lambda a: action_evs[a])
            state_evs[state] = StateEV(optimal_action, action_evs)

        return state_evs

    def _initialize_terminal_states(
        self, transitions: dict[State, dict[Action, dict[State, int]]], state_evs: dict[State, StateEV]
    ) -> None:
        for outcome in self.rules.get_possible_outcomes():
            terminal_state = TerminalState(outcome)
            payout = self.rules.get_outcome_payout(outcome)
            state_evs[terminal_state] = StateEV(Action.GAME_END, {Action.GAME_END: payout})

    def _calculate_action_evs(
        self, state: State, actions: dict[Action, dict[State, int]], state_evs: dict[State, StateEV]
    ) -> dict[Action, float]:
        action_evs = {
            action: self._calculate_single_action_ev(action, next_states, state_evs)
            for action, next_states in actions.items()
        }

        if not action_evs:
            raise ValueError(f"No actions found for state {state}")

        return action_evs

    def _calculate_single_action_ev(
        self, action: Action, next_states: dict[State, int], state_evs: dict[State, StateEV]
    ) -> float:
        if not next_states:
            raise ValueError(f"Action {action} has no next states")

        total_count = sum(next_states.values())

        return sum(
            self._get_state_ev(next_state, state_evs) * (count / total_count)
            for next_state, count in next_states.items()
        )

    def _get_state_ev(self, state: State, state_evs: dict[State, StateEV]) -> float:
        assert state in state_evs, f"Next state {state} not found in state_evs. This is a bug."
        return state_evs[state].action_evs.get(Action.GAME_END, 0.0)

    def _topological_sort(self, transitions: dict[State, dict[Action, dict[State, int]]]) -> list[State]:
        sorter: TopologicalSorter = TopologicalSorter()
        all_states = set()

        for state, actions in transitions.items():
            all_states.add(state)
            for next_states in actions.values():
                for next_state in next_states:
                    all_states.add(next_state)
                    sorter.add(next_state, state)

        # Ensure all states are added (even if they have no outgoing edges)
        for state in all_states:
            sorter.add(state)

        try:
            sorted_states = list(sorter.static_order())
            return sorted_states
        except ValueError as e:
            raise ValueError(f"Graph contains cycles: {e}")
