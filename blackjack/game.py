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
                try:
                    player.hand.add_card(self.shoe.deal_card())
                except ValueError as e:
                    logging.error(f"Error dealing to player {player.name}: {e}")
            try:
                self.dealer.hand.add_card(self.shoe.deal_card())
            except ValueError as e:
                logging.error(f"Error dealing to dealer: {e}")

    def play_turn(self, player: Player, strategy: Strategy, name: str = "") -> None:
        if not name:
            name = player.name
        while True:
            hv = self.rules.hand_value(player.hand)
            if self.rules.is_bust(player.hand):
                logging.info(f"{name} busts with hand: {player.hand} ({hv})")
                break
            # Prevent hitting at 21
            if hv.value == 21:
                logging.info(f"{name} stands with hand: {player.hand} ({hv}) - cannot hit at 21")
                break
            actions = self.rules.available_actions(player.hand, {})
            if not actions:
                logging.info(f"{name} has no available actions with hand: {player.hand} ({hv})")
                break
            action = strategy.choose_action(player.hand, actions, {})
            logging.info(f"{name} chooses {action.name} with hand: {player.hand} ({hv})")
            if action == Action.HIT:
                try:
                    card = self.shoe.deal_card()
                    player.hand.add_card(card)
                    hv_new = self.rules.hand_value(player.hand)
                    logging.info(f"{name} receives: {card}. New hand: {player.hand} ({hv_new})")
                except ValueError as e:
                    logging.error(f"Error dealing to {name}: {e}")
                    break
            elif action == Action.STAND:
                logging.info(f"{name} stands with hand: {player.hand} ({hv})")
                break
            else:
                logging.critical(
                    f"No valid action available for {name} with hand {player.hand.cards}. Available actions: {actions}"
                )
                raise RuntimeError(
                    f"No valid action available for {name} with hand {player.hand.cards}. Available actions: {actions}"
                )

    def play_round(self) -> None:
        self.initial_deal()
        player_results: list[dict[str, bool]] = []
        for player in self.players:
            if player.strategy is None:
                raise ValueError(f"Player {player.name} has no strategy assigned.")
            self.play_turn(player, player.strategy, player.name)
            player_results.append(
                {
                    "bust": self.rules.is_bust(player.hand),
                    "blackjack": self.rules.is_blackjack(player.hand),
                }
            )
        # If all players busted or have blackjack, skip dealer turn
        if all(r["bust"] or r["blackjack"] for r in player_results):
            return
        self.play_turn(self.dealer, self.dealer_strategy, "Dealer")
