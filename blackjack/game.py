from typing import Callable, Optional

from blackjack.entities.hand import Hand
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.entities.state import (
    GraphState,
    NewSplitHandState,
    Outcome,
    PairState,
    PendingSplitHandState,
    PreDealState,
    ProperState,
    SplitState,
    TerminalState,
    Turn,
)
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.game_events import GameEvent, RoundResultEvent
from blackjack.gameplay.game_context import GameContext
from blackjack.gameplay.turn_handler import Decision
from blackjack.rules.base import HandValue, Rules
from blackjack.strategy.base import Strategy
from blackjack.turn.state_machine import StateMachine
from blackjack.turn.turn_state import TurnState


class Game:
    def __init__(
        self,
        player_strategy: Strategy,
        shoe: Shoe,
        rules: Rules,
        state_machine: StateMachine,
        dealer_strategy: Strategy,
        state_transition_graph: StateTransitionGraph,
        output_tracker: Optional[Callable[[GameEvent], None]] = None,
    ) -> None:
        player: Player = Player("Player", player_strategy)
        dealer: Player = Player("Dealer", dealer_strategy)
        self.game_context = GameContext(player, shoe, rules, dealer)
        self.state_machine = state_machine
        self.output_tracker = output_tracker or (lambda _: None)
        self.state_transition_graph = state_transition_graph

    def _make_graph_state(self, turn_state: TurnState) -> GraphState:
        # if we are in the mixed terminal state, we need to instantiate one
        # for the delta of win/loss (unless it already exists).
        if turn_state.handler.is_terminal():
            outcomes: list[Outcome] = turn_state.handler.get_outcomes(self.game_context, turn_state)
            if len(outcomes) != 1:
                raise RuntimeError(f"Expected exactly one outcome for terminal state {turn_state}, got: {outcomes}")

            return TerminalState(outcomes[0])

        dealer_upcard_rank = self.game_context.dealer.hand.cards[0].graph_rank
        turn = turn_state.turn

        return self._hand_to_graph_state(self.game_context.player.hand, turn, dealer_upcard_rank)

    def _hand_to_graph_state(self, hand: Hand, turn, dealer_upcard_rank) -> GraphState:
        hand_value: HandValue = self.game_context.rules.hand_value(hand)
        if hand.is_pair():
            return PairState(
                pair_rank=hand.cards[0].graph_rank,
                turn=turn,
                dealer_upcard=dealer_upcard_rank,
                split_count=len(self.game_context.player.hands) - 1,
            )
        return ProperState(
            player_hand_value=hand_value.value,
            player_hand_soft=hand_value.soft,
            dealer_upcard_rank=dealer_upcard_rank,
            turn=turn,
            split_count=len(self.game_context.player.hands) - 1,
        )

    def play_round(self) -> StateTransitionGraph:
        turn_state: TurnState = TurnState.PRE_DEAL
        graph_states: list[GraphState] = [PreDealState()]
        graph_index: int = 0

        while not turn_state.handler.is_terminal():
            decision, action = turn_state.handler.handle_turn(turn_state, self.game_context, self.output_tracker)
            next_turn_state: TurnState = self.state_machine.transition(turn_state, decision)

            player_card = self.game_context.player.hand.cards[0].graph_rank
            dealer_upcard_rank = self.game_context.dealer.hand.cards[0].graph_rank
            split_count = len(self.game_context.player.hands) - 1

            if turn_state == TurnState.NEXT_SPLIT_HAND and decision == Decision.YES:
                assert (
                    self.game_context.has_split()
                ), "Expected game context to have a split given transitioning to next hand"

                graph_index += 1
                next_graph_state: GraphState = NewSplitHandState(
                    player_card=player_card,
                    dealer_upcard_rank=dealer_upcard_rank,
                    split_count=split_count,
                )
                self.state_transition_graph.add_transition(graph_states[graph_index], action, next_graph_state)
                graph_states[graph_index] = next_graph_state
            elif decision == Decision.SPLIT:
                next_graph_state = NewSplitHandState(
                    player_card=player_card,
                    dealer_upcard_rank=dealer_upcard_rank,
                    split_count=split_count,
                )

                later_graph_state: PendingSplitHandState = PendingSplitHandState(
                    player_card=player_card,
                    dealer_upcard_rank=dealer_upcard_rank,
                    min_split_count=split_count,
                )

                self.state_transition_graph.add_transition(
                    graph_states[graph_index], action, SplitState(next_graph_state, later_graph_state)
                )
                graph_states.append(later_graph_state)
                graph_states[graph_index] = next_graph_state
            elif next_turn_state == TurnState.GAME_OVER_SPLIT:
                turn_state = next_turn_state
                continue  # we will compute terminal states below
            else:
                next_graph_state = self._make_graph_state(next_turn_state)

                if next_turn_state.turn != Turn.DEALER:
                    if next_graph_state != graph_states[graph_index]:
                        self.state_transition_graph.add_transition(graph_states[graph_index], action, next_graph_state)
                        graph_states[graph_index] = next_graph_state

                    turn_state = next_turn_state
                    continue

                for i, source_node in enumerate(graph_states):
                    if isinstance(source_node, TerminalState):
                        continue

                    # TODO: should we only count this once per unique transition?
                    if next_graph_state != graph_states[graph_index]:
                        self.state_transition_graph.add_transition(graph_states[i], action, next_graph_state)
                        graph_states[i] = next_graph_state

            turn_state = next_turn_state

        player: Player = self.game_context.player
        outcomes: list[Outcome] = turn_state.handler.get_outcomes(self.game_context, turn_state)
        assert (
            len(outcomes) == len(graph_states) == len(player.hands)
        ), f"Mismatch in outcomes and graph states length {turn_state=} {outcomes=} {graph_states=} {player.hands=}"

        for i, outcome in enumerate(outcomes):
            source_state = graph_states[i]
            if isinstance(source_state, TerminalState):
                if source_state.outcome != outcome:
                    raise RuntimeError(
                        f"Graph state {source_state} already has outcome {source_state.outcome}, "
                        f"but got new outcome {outcome}"
                    )

                self.output_tracker(RoundResultEvent(player.name, player.hands[i].cards, outcome))
                continue

            terminal_state: TerminalState = TerminalState(outcome)
            self.state_transition_graph.add_transition(graph_states[i], action, terminal_state)
            self.output_tracker(RoundResultEvent(player.name, player.hands[i].cards, outcome))
            graph_states[i] = terminal_state

        self.output_tracker(RoundResultEvent(self.game_context.dealer.name, self.game_context.dealer.hand.cards, None))

        assert (
            graph_index == len(graph_states) - 1
        ), f"Graph index {graph_index} should match the length of graph states {len(graph_states)}"
        assert all(
            isinstance(state, TerminalState) for state in graph_states
        ), f"All split source nodes should be terminal states at the end of a round, got: {graph_states}"

        return self.state_transition_graph
