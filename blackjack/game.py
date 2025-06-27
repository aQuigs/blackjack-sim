import logging
from typing import Callable, Optional

from blackjack.action import Action
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.entities.state import ProperState, TerminalState, Turn
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
        player_strategies: list[Strategy],
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
        self.event_log: list[GameEvent] = []
        self._output_tracker = output_tracker or self.event_log.append
        self.state_transition_graph = StateTransitionGraph()

    def _track(self, event: GameEvent) -> None:
        self._output_tracker(event)

    def _make_proper_state(self, hand, is_player) -> ProperState:
        hv = self.rules.hand_value(hand)
        return ProperState(
            player_hand_value=hv.value,
            player_hand_soft=hv.soft,
            dealer_upcard_rank=self.dealer.hand.cards[0].rank,
            turn=Turn.PLAYER if is_player else Turn.DEALER,
        )

    def initial_deal(self) -> None:
        for _ in range(2):
            for player in self.players:
                card = self.shoe.deal_card()
                player.hand.add_card(card)
                self._track(GameEvent(GameEventType.DEAL, DealEvent(to=player.name, card=repr(card))))

            card = self.shoe.deal_card()
            self.dealer.hand.add_card(card)
            self._track(GameEvent(GameEventType.DEAL, DealEvent(to=self.dealer.name, card=repr(card))))

    def play_player_turn(self, player: Player, strategy: Strategy) -> tuple[bool, ProperState]:
        prev_state = self._make_proper_state(player.hand, is_player=True)
        while True:
            hand_value = self.rules.hand_value(player.hand)

            if self.rules.is_bust(player.hand):
                self._track(
                    GameEvent(
                        GameEventType.BUST,
                        BustEvent(player=player.name, hand=repr(player.hand), value=hand_value.value),
                    )
                )

                logging.info(f"{player.name} busts with hand: {player.hand} ({hand_value})")
                return False, prev_state

            if self.rules.is_blackjack(player.hand):
                self._track(
                    GameEvent(
                        GameEventType.BLACKJACK,
                        BlackjackEvent(player=player.name, hand=repr(player.hand), value=hand_value.value),
                    )
                )
                logging.info(f"{player.name} has blackjack with hand: {player.hand} ({hand_value})")
                return False, prev_state

            if hand_value.value == 21:
                self._track(
                    GameEvent(GameEventType.TWENTY_ONE, TwentyOneEvent(player=player.name, hand=repr(player.hand)))
                )
                return True, prev_state

            actions = self.rules.available_actions(player.hand, {})
            if not actions:
                self._track(
                    GameEvent(GameEventType.NO_ACTIONS, NoActionsEvent(player=player.name, hand=repr(player.hand)))
                )
                return False, prev_state

            stand, next_state = self.do_player_action(player, strategy, prev_state, actions)
            prev_state = next_state
            if stand:
                return True, prev_state

    def do_player_action(
        self, player: Player, strategy: Strategy, prev_state: ProperState, actions: list[Action]
    ) -> tuple[bool, ProperState]:
        hand_value = self.rules.hand_value(player.hand)
        action = strategy.choose_action(player.hand, actions, {})
        self._track(
            GameEvent(
                GameEventType.CHOOSE_ACTION,
                ChooseActionEvent(
                    player=player.name,
                    action=action,
                    hand=repr(player.hand),
                ),
            )
        )
        logging.info(f"{player.name} chooses {action.name} with hand: {player.hand} ({hand_value})")

        if action == Action.STAND:
            next_state = self._make_proper_state(player.hand, is_player=False)
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
                    HitEvent(
                        player=player.name,
                        card=repr(card),
                        new_hand=repr(player.hand),
                        value=hv_new.value,
                    ),
                )
            )
            logging.info(f"{player.name} receives: {card}. " f"New hand: {player.hand} ({hv_new})")
            return False, next_state
        else:
            raise RuntimeError(
                f"No valid action available for {player.name} with hand {player.hand.cards}. "
                f"Available actions: {actions}"
            )

    def play_dealer_turn(self, dealer: Player, strategy: Strategy) -> None:
        while True:
            if self.rules.is_bust(dealer.hand):
                self._track(
                    GameEvent(
                        GameEventType.BUST,
                        BustEvent(
                            player=dealer.name,
                            hand=repr(dealer.hand),
                            value=self.rules.hand_value(dealer.hand).value,
                        ),
                    )
                )
                logging.info(f"{dealer.name} busts with hand: {dealer.hand} ({self.rules.hand_value(dealer.hand)})")
                return

            actions = self.rules.available_actions(dealer.hand, {})
            if not actions:
                raise RuntimeError(
                    f"No valid actions available for dealer with hand {dealer.hand.cards}. "
                    f"Available actions: {actions}"
                )

            action = strategy.choose_action(dealer.hand, actions, {})
            self._track(
                GameEvent(
                    GameEventType.CHOOSE_ACTION,
                    ChooseActionEvent(
                        player=dealer.name,
                        action=action,
                        hand=repr(dealer.hand),
                    ),
                )
            )
            if action == Action.STAND:
                return
            elif action == Action.HIT:
                card = self.shoe.deal_card()
                dealer.hand.add_card(card)
                self._track(
                    GameEvent(
                        GameEventType.HIT,
                        HitEvent(
                            player=dealer.name,
                            card=repr(card),
                            new_hand=repr(dealer.hand),
                            value=self.rules.hand_value(dealer.hand).value,
                        ),
                    )
                )
                logging.info(
                    f"{dealer.name} receives: {card}. "
                    f"New hand: {dealer.hand} ({self.rules.hand_value(dealer.hand)})"
                )
            else:
                raise RuntimeError(
                    f"Invalid action {action} for dealer with hand {dealer.hand.cards}. "
                    f"Available actions: {actions}"
                )

    def play_turns(self) -> dict[str, ProperState]:
        last_player_states = {}
        dealer_needed = False

        for player in self.players:
            needs_dealer, last_state = self.play_player_turn(player, player.strategy)
            last_player_states[player.name] = last_state
            if needs_dealer:
                dealer_needed = True

        if dealer_needed:
            self.play_dealer_turn(self.dealer, self.dealer_strategy)

        return last_player_states

    def compute_player_results(self) -> list[PlayerResult]:
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

        return player_results

    def play_round(self) -> GameResult:
        self.event_log.clear()
        self.initial_deal()

        last_player_states = self.play_turns()
        player_results = self.compute_player_results()

        dealer_hand = list(self.dealer.hand.cards)
        winner = Winner.NONE
        if len(self.players) == 1:
            # TODO clean up and remove

            player = self.players[0]
            # Use rules to determine winner
            player_bust = self.rules.is_bust(player.hand)
            dealer_bust = self.rules.is_bust(self.dealer.hand)
            if player_bust:
                winner = Winner.DEALER
            elif dealer_bust:
                winner = Winner.PLAYER
            else:
                player_value = self.rules.hand_value(player.hand).value
                dealer_value = self.rules.hand_value(self.dealer.hand).value
                if player_value > dealer_value:
                    winner = Winner.PLAYER
                elif player_value < dealer_value:
                    winner = Winner.DEALER
                else:
                    winner = Winner.PUSH

        for player in self.players:
            last_state = last_player_states[player.name]
            if isinstance(last_state, ProperState):
                final_outcome = self.rules.determine_outcome(player.hand, self.dealer.hand)
                self.state_transition_graph.add_transition(last_state, Action.GAME_END, TerminalState(final_outcome))

        return GameResult(
            player_results=player_results,
            dealer_hand=dealer_hand,
            winner=winner,
            state_transition_graph=self.state_transition_graph,
        )
