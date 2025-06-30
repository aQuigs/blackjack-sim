import logging
from typing import Callable, Optional

from blackjack.entities.hand import Hand
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.entities.state import PreDealState, ProperState, State, TerminalState, Turn
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.game_events import (
    BlackjackEvent,
    BustEvent,
    ChooseActionEvent,
    DealEvent,
    GameEvent,
    HitEvent,
    TwentyOneEvent,
)
from blackjack.gameplay.game_context import GameContext
from blackjack.rules.base import Rules
from blackjack.strategy.base import Strategy
from blackjack.turn.action import Action
from blackjack.turn.state_machine import StateMachine
from blackjack.turn.turn_state import TurnState


class Game:
    def __init__(
        self,
        player_strategy: Strategy,
        shoe: Shoe,
        rules: Rules,
        dealer_strategy: Strategy,
        state_machine: StateMachine,
        state_transition_graph: StateTransitionGraph,
        output_tracker: Optional[Callable[[GameEvent], None]] = None,
    ) -> None:
        player: Player = Player("Player", player_strategy)
        dealer: Player = Player("Dealer", dealer_strategy)
        self.game_context = GameContext(player, shoe, rules, dealer)
        self.state_machine = state_machine
        self.output_tracker = output_tracker or (lambda _: None)
        self.state_transition_graph = state_transition_graph

    def _track(self, event: GameEvent) -> None:
        self.output_tracker(event)

    def _make_graph_state(self, hand: Hand, is_player: bool) -> ProperState:
        hand_value = self.game_context.rules.hand_value(hand)
        return ProperState(
            player_hand_value=hand_value.value,
            player_hand_soft=hand_value.soft,
            dealer_upcard_rank=self.game_context.rules.translate_upcard(self.game_context.dealer.hand.cards[0]),
            turn=Turn.PLAYER if is_player else Turn.DEALER,
        )

    def play_round(self) -> StateTransitionGraph:
        turn_state: TurnState = TurnState.PRE_DEAL
        graph_state: State = PreDealState()

        while not turn_state.value.is_terminal():
            decision, action = turn_state.value.handle_turn(self.game_context, self.output_tracker)
            next_turn_state: TurnState = self.state_machine.transition(turn_state, decision)
            next_graph_state: State = self._make_graph_state(self.game_context)
            if next_graph_state != graph_state:
                if action is None:
                    raise Exception(f"Graph state changed but action was None. {turn_state=} {next_turn_state=} {decision=}")

                self.state_transition_graph.add_transition(graph_state, action, next_graph_state)
                graph_state = next_graph_state

            turn_state = next_turn_state

        if not isinstance(graph_state, TerminalState):
            raise RuntimeError(f"Final graph state must be terminal, got {graph_state}")

        # TODO include this in the handlers
        # for player in self.players:
        #     hand = list(player.hand.cards)
        #     outcome = self.rules.determine_outcome(player.hand, self.dealer.hand)

        #     last_state = last_player_states[player.name]
        #     if isinstance(last_state, ProperState):
        #         final_outcome = self.rules.determine_outcome(player.hand, self.dealer.hand)
        #         self.state_transition_graph.add_transition(last_state, Action.GAME_END, TerminalState(final_outcome))

        #     self._track(
        #         RoundResultEvent(
        #             name=player.name,
        #             hand=hand,
        #             outcome=outcome,
        #         )
        #     )

        # # Emit ROUND_RESULT for dealer (no outcome)
        # dealer_hand = list(self.dealer.hand.cards)
        # self._track(RoundResultEvent(name=self.dealer.name, hand=dealer_hand, outcome=None))

        return self.state_transition_graph
