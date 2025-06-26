import logging
from typing import Callable, List, Optional, Sequence

from blackjack.action import Action
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.entities.state import Outcome, ProperState, TerminalState, Turn
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.game_events import (
    BlackjackEvent,
    BustEvent,
    ChooseActionEvent,
    DealEvent,
    GameEvent,
    GameEventType,
    GameResult,
    HitEvent,
    InvalidActionEvent,
    NoActionsEvent,
    PlayerOutcome,
    PlayerResult,
    TwentyOneEvent,
    Winner,
)
from blackjack.rules.base import Rules
from blackjack.strategy.base import Strategy


class Game:
    def __init__(
        self,
        player_strategies: Sequence[Strategy],
        shoe: Shoe,
        rules: Rules,
        dealer_strategy: Strategy,
        output_tracker: Optional[Callable[[GameEvent], None]] = None,
    ) -> None:
        self.shoe: Shoe = shoe
        self.rules: Rules = rules
        self.players: list[Player] = [Player(f"Player {i+1}", strategy) for i, strategy in enumerate(player_strategies)]
        self.dealer: Player = Player("Dealer", dealer_strategy)
        self.dealer_strategy: Strategy = dealer_strategy
        self.event_log: List[GameEvent] = []
        self._output_tracker = output_tracker or self.event_log.append
        self.state_transition_graph = StateTransitionGraph()

    def _track(self, event: GameEvent) -> None:
        self._output_tracker(event)

    def _make_proper_state(self, hand, is_player):
        hand_value = self.rules.hand_value(hand)
        upcard = self.dealer.hand.cards[0] if self.dealer.hand.cards else None
        upcard_rank = upcard.rank if upcard else None
        turn = Turn.PLAYER if is_player else Turn.DEALER
        return ProperState(
            player_hand_value=hand_value.value,
            player_hand_soft=hand_value.soft,
            dealer_upcard_rank=upcard_rank,
            turn=turn,
        )

    def get_state_transition_graph(self):
        return self.state_transition_graph

    def initial_deal(self) -> None:
        for _ in range(2):
            for player in self.players:
                card = self.shoe.deal_card()
                player.hand.add_card(card)
                self._track(GameEvent(GameEventType.DEAL, DealEvent(to=player.name, card=repr(card))))

            card = self.shoe.deal_card()
            self.dealer.hand.add_card(card)
            self._track(GameEvent(GameEventType.DEAL, DealEvent(to=self.dealer.name, card=repr(card))))

    def play_turn(self, player: Player, strategy: Strategy) -> bool:
        prev_state = self._make_proper_state(player.hand, is_player=True)
        while True:
            hand_value = self.rules.hand_value(player.hand)

            if self.rules.is_bust(player.hand):
                outcome_state = TerminalState(Outcome.LOSE)
                self.state_transition_graph.add_transition(prev_state, Action.GAME_END, outcome_state)
                self._track(
                    GameEvent(
                        GameEventType.BUST,
                        BustEvent(player=player.name, hand=repr(player.hand), value=hand_value.value),
                    )
                )
                logging.info(f"{player.name} busts with hand: {player.hand} ({hand_value})")
                return False

            if self.rules.is_blackjack(player.hand):
                outcome_state = TerminalState(Outcome.WIN)
                self.state_transition_graph.add_transition(prev_state, Action.GAME_END, outcome_state)
                self._track(
                    GameEvent(
                        GameEventType.BLACKJACK,
                        BlackjackEvent(player=player.name, hand=repr(player.hand), value=hand_value.value),
                    )
                )
                logging.info(f"{player.name} has blackjack with hand: {player.hand} ({hand_value})")
                return False

            if hand_value.value == 21:
                outcome_state = TerminalState(Outcome.WIN)
                self.state_transition_graph.add_transition(prev_state, Action.GAME_END, outcome_state)
                self._track(
                    GameEvent(GameEventType.TWENTY_ONE, TwentyOneEvent(player=player.name, hand=repr(player.hand)))
                )
                return True

            # Get available actions and check if there are any
            actions = self.rules.available_actions(player.hand, {})
            if not actions:
                self._track(
                    GameEvent(GameEventType.NO_ACTIONS, NoActionsEvent(player=player.name, hand=repr(player.hand)))
                )
                return False

            action_taken = self.do_player_action(player, strategy, prev_state, actions)
            if action_taken[0]:
                return True
            prev_state = action_taken[1]

    def do_player_action(
        self, player: Player, strategy: Strategy, prev_state: ProperState, actions: list[Action]
    ) -> tuple[bool, ProperState]:
        hand_value = self.rules.hand_value(player.hand)
        action = strategy.choose_action(player.hand, actions, {})
        self._track(
            GameEvent(
                GameEventType.CHOOSE_ACTION,
                ChooseActionEvent(player=player.name, action=action, hand=repr(player.hand)),
            )
        )
        logging.info(f"{player.name} chooses {action.name} with hand: {player.hand} ({hand_value})")

        if action == Action.STAND:
            next_state = self._make_proper_state(player.hand, is_player=True)
            self.state_transition_graph.add_transition(prev_state, action, next_state)
            return True, next_state
        elif action == Action.HIT:
            card = self.shoe.deal_card()
            player.hand.add_card(card)
            hv_new = self.rules.hand_value(player.hand)
            next_state = self._make_proper_state(player.hand, is_player=True)
            self.state_transition_graph.add_transition(prev_state, action, next_state)
            self._track(
                GameEvent(
                    GameEventType.HIT,
                    HitEvent(player=player.name, card=repr(card), new_hand=repr(player.hand), value=hv_new.value),
                )
            )
            logging.info(f"{player.name} receives: {card}. New hand: {player.hand} ({hv_new})")
            return False, next_state
        else:
            self._track(
                GameEvent(
                    GameEventType.INVALID_ACTION,
                    InvalidActionEvent(
                        player=player.name,
                        action=getattr(action, "name", str(action)),
                        hand=repr(player.hand),
                    ),
                )
            )
            raise RuntimeError(
                f"No valid action available for {player.name} with hand {player.hand.cards}. "
                f"Available actions: {actions}"
            )

    def play_round(self) -> GameResult:
        self.event_log.clear()
        self.initial_deal()
        dealer_needed = False

        for player in self.players:
            if self.play_turn(player, player.strategy):
                dealer_needed = True

        if dealer_needed:
            self.play_turn(self.dealer, self.dealer_strategy)

        # Compute structured result
        player_results = []
        for player in self.players:
            hand = list(player.hand.cards)
            if self.rules.is_bust(player.hand):
                outcome = PlayerOutcome.BUST
            elif self.rules.is_blackjack(player.hand):
                outcome = PlayerOutcome.BLACKJACK
            else:
                outcome = PlayerOutcome.ACTIVE
            player_results.append(PlayerResult(name=player.name, hand=hand, outcome=outcome))

        dealer_hand = list(self.dealer.hand.cards)
        dealer_bust = self.rules.is_bust(self.dealer.hand)
        dealer_value = self.rules.hand_value(self.dealer.hand).value
        winner = Winner.NONE
        # Simple winner logic for single player
        if len(self.players) == 1:
            player = self.players[0]
            player_value = self.rules.hand_value(player.hand).value
            if self.rules.is_bust(player.hand):
                winner = Winner.DEALER
            elif dealer_bust:
                winner = Winner.PLAYER
            elif player_value > dealer_value:
                winner = Winner.PLAYER
            elif player_value < dealer_value:
                winner = Winner.DEALER
            else:
                winner = Winner.PUSH
        return GameResult(player_results=player_results, dealer_hand=dealer_hand, winner=winner)
