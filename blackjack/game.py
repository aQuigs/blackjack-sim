import logging
from typing import Sequence, List, Any, Optional, Callable
from enum import Enum, auto
from dataclasses import dataclass

from blackjack.action import Action
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.rules.base import Rules
from blackjack.strategy.base import Strategy


class GameEventType(Enum):
    DEAL = auto()
    BUST = auto()
    BLACKJACK = auto()
    TWENTY_ONE = auto()
    NO_ACTIONS = auto()
    CHOOSE_ACTION = auto()
    HIT = auto()
    INVALID_ACTION = auto()


class PlayerOutcome(Enum):
    BUST = auto()
    BLACKJACK = auto()
    ACTIVE = auto()


class Winner(Enum):
    DEALER = auto()
    PLAYER = auto()
    PUSH = auto()
    NONE = auto()


@dataclass(frozen=True)
class DealEvent:
    to: str
    card: str


@dataclass(frozen=True)
class BustEvent:
    player: str
    hand: str
    value: int


@dataclass(frozen=True)
class BlackjackEvent:
    player: str
    hand: str
    value: int


@dataclass(frozen=True)
class TwentyOneEvent:
    player: str
    hand: str


@dataclass(frozen=True)
class NoActionsEvent:
    player: str
    hand: str


@dataclass(frozen=True)
class ChooseActionEvent:
    player: str
    action: Action
    hand: str


@dataclass(frozen=True)
class HitEvent:
    player: str
    card: str
    new_hand: str
    value: int


@dataclass(frozen=True)
class InvalidActionEvent:
    player: str
    action: str
    hand: str


@dataclass(frozen=True)
class PlayerResult:
    name: str
    hand: List[str]
    outcome: PlayerOutcome


@dataclass(frozen=True)
class GameResult:
    player_results: List[PlayerResult]
    dealer_hand: List[str]
    winner: Optional[Winner]


@dataclass(frozen=True)
class GameEvent:
    type: GameEventType
    payload: Any


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

    def _track(self, event: GameEvent) -> None:
        self._output_tracker(event)

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
        while True:
            hand_value = self.rules.hand_value(player.hand)

            if self.rules.is_bust(player.hand):
                self._track(GameEvent(GameEventType.BUST, BustEvent(player=player.name, hand=repr(player.hand), value=hand_value.value)))
                logging.info(f"{player.name} busts with hand: {player.hand} ({hand_value})")
                return False

            if self.rules.is_blackjack(player.hand):
                self._track(GameEvent(GameEventType.BLACKJACK, BlackjackEvent(player=player.name, hand=repr(player.hand), value=hand_value.value)))
                logging.info(f"{player.name} has blackjack with hand: {player.hand} ({hand_value})")
                return False

            if hand_value.value == 21:
                self._track(GameEvent(GameEventType.TWENTY_ONE, TwentyOneEvent(player=player.name, hand=repr(player.hand))))
                return True

            if self.do_player_action(player, strategy):
                return True

    def do_player_action(self, player: Player, strategy: Strategy) -> bool:
        hand_value = self.rules.hand_value(player.hand)
        actions = self.rules.available_actions(player.hand, {})
        if not actions:
            self._track(GameEvent(GameEventType.NO_ACTIONS, NoActionsEvent(player=player.name, hand=repr(player.hand))))
            raise RuntimeError(f"{player.name} has no available actions with hand: {player.hand} ({hand_value})")

        action = strategy.choose_action(player.hand, actions, {})
        self._track(GameEvent(GameEventType.CHOOSE_ACTION, ChooseActionEvent(player=player.name, action=action, hand=repr(player.hand))))
        logging.info(f"{player.name} chooses {action.name} with hand: {player.hand} ({hand_value})")

        if action == Action.STAND:
            return True
        elif action == Action.HIT:
            card = self.shoe.deal_card()
            player.hand.add_card(card)
            hv_new = self.rules.hand_value(player.hand)
            self._track(GameEvent(GameEventType.HIT, HitEvent(player=player.name, card=repr(card), new_hand=repr(player.hand), value=hv_new.value)))
            logging.info(f"{player.name} receives: {card}. New hand: {player.hand} ({hv_new})")
            return False
        else:
            self._track(
                GameEvent(
                    GameEventType.INVALID_ACTION,
                    InvalidActionEvent(
                        player=player.name,
                        action=getattr(action, 'name', str(action)),
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
            hand = [repr(card) for card in player.hand.cards]
            if self.rules.is_bust(player.hand):
                outcome = PlayerOutcome.BUST
            elif self.rules.is_blackjack(player.hand):
                outcome = PlayerOutcome.BLACKJACK
            else:
                outcome = PlayerOutcome.ACTIVE
            player_results.append(PlayerResult(name=player.name, hand=hand, outcome=outcome))

        dealer_hand = [repr(card) for card in self.dealer.hand.cards]
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
