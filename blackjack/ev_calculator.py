from dataclasses import dataclass
from graphlib import TopologicalSorter

from blackjack.entities.state import SplitState, GraphState, TerminalState, NewSplitHandState, PendingSplitHandState
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.rules.base import Rules
from blackjack.turn.action import Action

EV_MULTIPLIER: dict[Action, int] = {
    Action.DOUBLE: 2,
}


@dataclass(frozen=True)
class StateEV:
    optimal_action: Action
    action_evs: dict[Action, float]
    total_count: int


class EVCalculator:
    def __init__(self, rules: Rules):
        self.rules = rules

    def calculate_evs(self, graph: StateTransitionGraph) -> dict[GraphState, StateEV]:
        transitions = graph.get_graph()

        if not transitions:
            return {}

        state_evs: dict[GraphState, StateEV] = {}

        self._initialize_terminal_states(transitions, state_evs)
        sorted_states = self._topological_sort(transitions)

        for state in reversed(sorted_states):
            if isinstance(state, TerminalState):
                continue

            if isinstance(state, SplitState):
                # For split states, calculate EV as the sum of both hands states
                action_evs = {Action.NOOP: self._get_state_ev(state.first_hand_state, state_evs) + self._get_state_ev(state.second_hand_state, state_evs)}
                state_evs[state] = StateEV(Action.NOOP, action_evs, 0)
                continue

            if state not in transitions:
                raise ValueError(f"State {state} is in the graph but not in transitions. This is a bug.")

            action_evs = self._calculate_action_evs(state, transitions[state], state_evs)

            optimal_action = max(action_evs, key=lambda a: action_evs[a])
            total_count = sum(sum(next_states.values()) for next_states in transitions[state].values())
            state_evs[state] = StateEV(optimal_action, action_evs, total_count)

        return state_evs

    def _initialize_terminal_states(
        self, transitions: dict[GraphState, dict[Action, dict[GraphState, int]]], state_evs: dict[GraphState, StateEV]
    ) -> None:
        for outcome in self.rules.get_possible_outcomes():
            terminal_state = TerminalState(outcome)
            payout = self.rules.get_outcome_payout(outcome)
            state_evs[terminal_state] = StateEV(Action.NOOP, {Action.NOOP: payout}, 0)

    def _calculate_action_evs(
        self, state: GraphState, actions: dict[Action, dict[GraphState, int]], state_evs: dict[GraphState, StateEV]
    ) -> dict[Action, float]:
        action_evs = {
            action: self._calculate_single_action_ev(action, next_states, state_evs)
            for action, next_states in actions.items()
        }

        if not action_evs:
            raise ValueError(f"No actions found for state {state}")

        if Action.NOOP in action_evs and len(action_evs) > 1:
            raise ValueError(f"State {state} has NOOP action but also other actions. This is a bug. {action_evs=}")

        return action_evs

    def _calculate_single_action_ev(
        self, action: Action, next_states: dict[GraphState, int], state_evs: dict[GraphState, StateEV]
    ) -> float:
        if not next_states:
            raise ValueError(f"Action {action} has no next states")

        total_count = sum(next_states.values())

        return sum(
            self._get_state_ev(next_state, state_evs) * (count / total_count) * EV_MULTIPLIER.get(action, 1)
            for next_state, count in next_states.items()
        )

    def _get_state_ev(self, state: GraphState, state_evs: dict[GraphState, StateEV]) -> float:
        assert state in state_evs, f"Next state {state} not found in state_evs. This is a bug."
        state_ev = state_evs[state]
        return state_ev.action_evs[state_ev.optimal_action]

    def _topological_sort(self, transitions: dict[GraphState, dict[Action, dict[GraphState, int]]]) -> list[GraphState]:
        sorter: TopologicalSorter = TopologicalSorter()
        all_states = set()

        for state, actions in transitions.items():
            all_states.add(state)
            for next_states in actions.values():
                for next_state in next_states:
                    all_states.add(next_state)
                    sorter.add(next_state, state)

                    # Ensure SplitState is processed after its component states
                    if isinstance(next_state, SplitState):
                        sorter.add(next_state.first_hand_state, next_state)
                        sorter.add(next_state.second_hand_state, next_state)

        # Ensure all states are added (even if they have no outgoing edges)
        for state in all_states:
            sorter.add(state)

        try:
            sorted_states = list(sorter.static_order())
            return sorted_states
        except ValueError as e:
            raise ValueError(f"Graph contains cycles: {e}")
