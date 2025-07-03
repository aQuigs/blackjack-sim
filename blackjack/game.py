from typing import Callable, Optional

from blackjack.gameplay.turn_handler import Decision
from blackjack.entities.hand import Hand
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.entities.state import (
    CompoundState,
    CompoundTerminalState,
    GraphState,
    NewSplitHandState,
    Outcome,
    PairState,
    PendingSplitHandState,
    PreDealState,
    ProperState,
    TerminalState,
)
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.game_events import GameEvent, RoundResultEvent
from blackjack.gameplay.game_context import GameContext
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
            if len(outcomes) == 1:
                return TerminalState(outcomes[0])

            return CompoundTerminalState(tuple(TerminalState(outcome) for outcome in outcomes))

        dealer_upcard_rank = self.game_context.dealer.hand.cards[0].graph_rank
        turn = turn_state.turn

        if not self.game_context.has_split():
            return self._hand_to_graph_state(self.game_context.player.hand, turn, dealer_upcard_rank)

        hand_states = tuple(
            self._hand_to_graph_state(hand, turn, dealer_upcard_rank) for hand in self.game_context.player.hands
        )
        return CompoundState(
            active_index=self.game_context.player.active_index,
            hand_states=hand_states,
            dealer_upcard_rank=dealer_upcard_rank,
            turn=turn,
        )

    def _hand_to_graph_state(self, hand: Hand, turn, dealer_upcard_rank) -> GraphState:
        hand_value: HandValue = self.game_context.rules.hand_value(hand)
        if hand.is_pair():
            return PairState(
                pair_rank=hand.cards[0].graph_rank,
                turn=turn,
                dealer_upcard=dealer_upcard_rank,
            )
        return ProperState(
            player_hand_value=hand_value.value,
            player_hand_soft=hand_value.soft,
            dealer_upcard_rank=dealer_upcard_rank,
            turn=turn,
        )

    def play_round(self) -> StateTransitionGraph:
        turn_state: TurnState = TurnState.PRE_DEAL
        graph_state: GraphState = PreDealState()
        pending_split_stack: list[PendingSplitHandState] = []
        split_source_nodes: list[GraphState] = []

        while not turn_state.handler.is_terminal():
            decision, action = turn_state.handler.handle_turn(turn_state, self.game_context, self.output_tracker)
            next_turn_state: TurnState = self.state_machine.transition(turn_state, decision)

            if turn_state == TurnState.NEXT_SPLIT_HAND and self.game_context.has_split():
                # add a node to node for moving to the state as if the decision was no
                # if decision was yes, pop from stack and transition to a NewSPlitHandState. set that to graph_state
                # add the latest to the split_source_nodes
                # then, if decision is yes we move forward
                # if decision is no we also move fwd
                # so just turn_state = next_turn_state

                pass

            elif decision == Decision.SPLIT:
                player_card = self.game_context.player.hand.cards[0].graph_rank
                dealer_upcard_rank = self.game_context.dealer.hand.cards[0].graph_rank
                split_count = len(self.game_context.player.hands) - 1

                next_graph_state: GraphState = NewSplitHandState(
                    player_card=player_card,
                    dealer_upcard_rank=dealer_upcard_rank,
                    split_count=split_count,
                )

                later_graph_state: PendingSplitHandState = PendingSplitHandState(
                    player_card=player_card,
                    dealer_upcard_rank=dealer_upcard_rank,
                    min_split_count=split_count,
                )

                pending_split_stack.append(later_graph_state)
                self.state_transition_graph.add_transition(graph_state, action, [next_graph_state, later_graph_state])
                graph_state = next_graph_state
            elif decision == Decision.MIX:
                # terminal outcome thing
                pass
            else:
                next_graph_state = self._make_graph_state(next_turn_state)
                if next_graph_state != graph_state:
                    self.state_transition_graph.add_transition(graph_state, action, next_graph_state)
                    graph_state = next_graph_state

            turn_state = next_turn_state

        if not (isinstance(graph_state, TerminalState) or isinstance(graph_state, CompoundTerminalState)):
            raise RuntimeError(f"Final graph state must be terminal, got {graph_state}")

        outcomes: tuple[Outcome] = turn_state.handler.get_outcomes(self.game_context, turn_state)
        for hand, outcome in zip(self.game_context.player.hands, outcomes):
            self.output_tracker(RoundResultEvent(self.game_context.player.name, hand.cards, outcome))

        self.output_tracker(RoundResultEvent(self.game_context.dealer.name, self.game_context.dealer.hand.cards, None))

        assert len(pending_split_stack) == 0, f"Pending split stack should be empty at the end of a round, got {pending_split_stack}"
        assert all(isinstance(state, TerminalState) for state in split_source_nodes), (
            f"All split source nodes should be terminal states at the end of a round, got: {split_source_nodes}"
        )

        return self.state_transition_graph
