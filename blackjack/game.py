import logging
from typing import Callable, Optional

from blackjack.action import Action
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.entities.state import PreDealState, ProperState, TerminalState, Turn
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.game_events import (
    BlackjackEvent,
    BustEvent,
    ChooseActionEvent,
    DealEvent,
    GameEvent,
    GameEventType,
    HitEvent,
    RoundResultEvent,
    TwentyOneEvent,
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
        state_transition_graph: StateTransitionGraph,
        output_tracker: Optional[Callable[[GameEvent], None]] = None,
    ) -> None:
        self.shoe: Shoe = shoe
        self.rules: Rules = rules
        self.players: list[Player] = [Player(f"Player {i+1}", strategy) for i, strategy in enumerate(player_strategies)]
        self.dealer: Player = Player("Dealer", dealer_strategy)
        self.dealer_strategy: Strategy = dealer_strategy
        self.output_tracker = output_tracker or (lambda _: None)
        self.state_transition_graph = state_transition_graph

    def _track(self, event: GameEvent) -> None:
        self.output_tracker(event)

    def _make_proper_state(self, hand, is_player) -> ProperState:
        hand_value = self.rules.hand_value(hand)
        return ProperState(
            player_hand_value=hand_value.value,
            player_hand_soft=hand_value.soft,
            dealer_upcard_rank=self.dealer.hand.cards[0].rank,
            turn=Turn.PLAYER if is_player else Turn.DEALER,
        )

    def initial_deal(self) -> None:
        for _ in range(2):
            for player in self.players:
                card = self.shoe.deal_card()
                player.hand.add_card(card)
                self._track(GameEvent(GameEventType.DEAL, DealEvent(to=player.name, card=card)))

            card = self.shoe.deal_card()
            self.dealer.hand.add_card(card)
            self._track(GameEvent(GameEventType.DEAL, DealEvent(to=self.dealer.name, card=card)))

        pre_deal_state = PreDealState()
        for player in self.players:
            initial_state = self._make_proper_state(player.hand, is_player=True)
            self.state_transition_graph.add_transition(pre_deal_state, Action.DEAL, initial_state)

    def play_player_turn(self, player: Player, strategy: Strategy) -> tuple[bool, ProperState]:
        prev_state = self._make_proper_state(player.hand, is_player=True)
        while True:
            hand_value = self.rules.hand_value(player.hand)

            if self.rules.is_bust(player.hand):
                self._track(
                    GameEvent(
                        GameEventType.BUST,
                        BustEvent(player=player.name, hand=player.hand.cards.copy(), value=hand_value.value),
                    )
                )

                logging.info(f"{player.name} busts with hand: {player.hand} ({hand_value})")
                return False, prev_state

            if self.rules.is_blackjack(player.hand):
                self._track(
                    GameEvent(
                        GameEventType.BLACKJACK,
                        BlackjackEvent(player=player.name, hand=player.hand.cards.copy()),
                    )
                )
                logging.info(f"{player.name} has blackjack with hand: {player.hand} ({hand_value})")
                return False, prev_state

            if hand_value.value == 21:
                self._track(
                    GameEvent(
                        GameEventType.TWENTY_ONE, TwentyOneEvent(player=player.name, hand=player.hand.cards.copy())
                    )
                )
                return True, prev_state

            actions = self.rules.available_actions(player.hand, {})
            if not actions:
                raise RuntimeError(
                    f"No valid actions available for {player.name} with hand {player.hand.cards}. "
                    f"Available actions: {actions}"
                )

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
                ChooseActionEvent(player=player.name, action=action, hand=player.hand.cards.copy()),
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
            new_hand_value = self.rules.hand_value(player.hand)
            next_state = self._make_proper_state(player.hand, is_player=True)
            self.state_transition_graph.add_transition(prev_state, action, next_state)
            self._track(
                GameEvent(
                    GameEventType.HIT,
                    HitEvent(
                        player=player.name,
                        card=card,
                        new_hand=player.hand.cards.copy(),
                        value=new_hand_value.value,
                    ),
                )
            )
            logging.info(f"{player.name} receives: {card}. New hand: {player.hand} ({new_hand_value})")
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
                            hand=dealer.hand.cards.copy(),
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
                    ChooseActionEvent(player=dealer.name, action=action, hand=dealer.hand.cards.copy()),
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
                            card=card,
                            new_hand=dealer.hand.cards.copy(),
                            value=self.rules.hand_value(dealer.hand).value,
                        ),
                    )
                )
                logging.info(
                    f"{dealer.name} receives: {card}. New hand: {dealer.hand} ({self.rules.hand_value(dealer.hand)})"
                )
                continue
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

    def play_round(self) -> StateTransitionGraph:
        self.initial_deal()

        last_player_states = self.play_turns()

        for player in self.players:
            hand = list(player.hand.cards)
            outcome = self.rules.determine_outcome(player.hand, self.dealer.hand)

            last_state = last_player_states[player.name]
            if isinstance(last_state, ProperState):
                final_outcome = self.rules.determine_outcome(player.hand, self.dealer.hand)
                self.state_transition_graph.add_transition(last_state, Action.GAME_END, TerminalState(final_outcome))

            self._track(
                GameEvent(
                    GameEventType.ROUND_RESULT,
                    RoundResultEvent(
                        name=player.name,
                        hand=hand,
                        outcome=outcome,
                    ),
                )
            )

        # Emit ROUND_RESULT for dealer (no outcome)
        dealer_hand = list(self.dealer.hand.cards)
        self._track(
            GameEvent(
                GameEventType.ROUND_RESULT, RoundResultEvent(name=self.dealer.name, hand=dealer_hand, outcome=None)
            )
        )

        return self.state_transition_graph
