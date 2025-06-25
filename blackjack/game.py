import logging
from typing import Sequence

from blackjack.action import Action
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.rules.base import Rules
from blackjack.strategy.base import Strategy


class Game:
    def __init__(
        self, player_strategies: Sequence[Strategy], shoe: Shoe, rules: Rules, dealer_strategy: Strategy
    ) -> None:
        self.shoe: Shoe = shoe
        self.rules: Rules = rules
        self.players: list[Player] = [Player(f"Player {i+1}", strategy) for i, strategy in enumerate(player_strategies)]
        self.dealer: Player = Player("Dealer", dealer_strategy)
        self.dealer_strategy: Strategy = dealer_strategy

    def initial_deal(self) -> None:
        for _ in range(2):
            for player in self.players:
                player.hand.add_card(self.shoe.deal_card())

            self.dealer.hand.add_card(self.shoe.deal_card())

    def play_turn(self, player: Player, strategy: Strategy) -> bool:
        while True:
            hand_value = self.rules.hand_value(player.hand)

            if self.rules.is_bust(player.hand):
                logging.info(f"{player.name} busts with hand: {player.hand} ({hand_value})")
                return False

            if self.rules.is_blackjack(player.hand):
                logging.info(f"{player.name} has blackjack with hand: {player.hand} ({hand_value})")
                return False

            if hand_value.value == 21:
                return True

            if self.do_player_action(player, strategy):
                return True

    def do_player_action(self, player: Player, strategy: Strategy) -> bool:
        hand_value = self.rules.hand_value(player.hand)
        actions = self.rules.available_actions(player.hand, {})
        if not actions:
            raise RuntimeError(f"{player.name} has no available actions with hand: {player.hand} ({hand_value})")

        action = strategy.choose_action(player.hand, actions, {})
        logging.info(f"{player.name} chooses {action.name} with hand: {player.hand} ({hand_value})")

        if action == Action.STAND:
            return True
        elif action == Action.HIT:
            card = self.shoe.deal_card()
            player.hand.add_card(card)
            hv_new = self.rules.hand_value(player.hand)

            logging.info(f"{player.name} receives: {card}. New hand: {player.hand} ({hv_new})")

            return False
        else:
            raise RuntimeError(
                f"No valid action available for {player.name} with hand {player.hand.cards}. "
                f"Available actions: {actions}"
            )

    def play_round(self) -> None:
        self.initial_deal()
        dealer_needed = False

        for player in self.players:
            if self.play_turn(player, player.strategy):
                dealer_needed = True

        if dealer_needed:
            self.play_turn(self.dealer, self.dealer_strategy)
