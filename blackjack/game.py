import logging
from typing import List

from blackjack.action import Action
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.rules.base import Rules
from blackjack.strategy.base import PlayerStrategy


class Game:
    def __init__(self, num_players: int, shoe: Shoe, rules: Rules):
        self.shoe = shoe
        self.rules = rules
        self.players = [Player(f"Player {i+1}") for i in range(num_players)]
        self.dealer = Player("Dealer")

    def initial_deal(self):
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

    def play_player_turn(self, player: Player, strategy: PlayerStrategy):
        while True:
            hv = self.rules.hand_value(player.hand)
            if self.rules.is_bust(player.hand):
                hand_str = [str(card) for card in player.hand.cards]
                msg = (
                    f"{player.name} busts with hand: {hand_str} "
                    f"({hv.value}{', soft' if hv.soft else ''})"
                )
                logging.info(msg)
                break
            actions = self.rules.available_actions(player.hand, {})
            if not actions:
                msg = (
                    f"{player.name} has no available actions with hand: "
                    f"{[str(card) for card in player.hand.cards]} "
                    f"({hv.value}{', soft' if hv.soft else ''})"
                )
                logging.info(msg)
                break
            action = strategy.choose_action(player.hand, actions, {})
            msg = (
                f"{player.name} chooses action: {action.name} with hand: "
                f"{[str(card) for card in player.hand.cards]} "
                f"({hv.value}{', soft' if hv.soft else ''})"
            )
            logging.info(msg)
            if action == Action.HIT:
                try:
                    card = self.shoe.deal_card()
                    player.hand.add_card(card)
                    hv_new = self.rules.hand_value(player.hand)
                    msg = (
                        f"{player.name} hits and receives: {card}. New hand: "
                        f"{[str(c) for c in player.hand.cards]} "
                        f"({hv_new.value}{', soft' if hv_new.soft else ''})"
                    )
                    logging.info(msg)
                except ValueError as e:
                    logging.error(f"Error dealing to player {player.name}: {e}")
                    break
            elif action == Action.STAND:
                msg = (
                    f"{player.name} stands with hand: "
                    f"{[str(card) for card in player.hand.cards]} "
                    f"({hv.value}{', soft' if hv.soft else ''})"
                )
                logging.info(msg)
                break
            else:
                logging.critical(
                    f"No valid action available for player {player.name} "
                    f"with hand {player.hand.cards}. Available actions: {actions}"
                )
                raise RuntimeError(
                    f"No valid action available for player {player.name} "
                    f"with hand {player.hand.cards}. Available actions: {actions}"
                )

    def play_dealer_turn(self):
        while self.rules.dealer_should_hit(self.dealer.hand):
            try:
                card = self.shoe.deal_card()
                self.dealer.hand.add_card(card)
                hv = self.rules.hand_value(self.dealer.hand)
                msg = (
                    f"Dealer hits and receives: {card}. New hand: "
                    f"{[str(c) for c in self.dealer.hand.cards]} "
                    f"({hv.value}{', soft' if hv.soft else ''})"
                )
                logging.info(msg)
            except ValueError as e:
                logging.error(f"Error dealing to dealer: {e}")
                break
        hv = self.rules.hand_value(self.dealer.hand)
        msg = (
            f"Dealer stands with hand: "
            f"{[str(card) for card in self.dealer.hand.cards]} "
            f"({hv.value}{', soft' if hv.soft else ''})"
        )
        logging.info(msg)

    def play_round(self, strategies: List[PlayerStrategy]):
        if len(strategies) != len(self.players):
            raise ValueError("Number of strategies must match number of players.")
        self.initial_deal()
        player_results = []
        for player, strategy in zip(self.players, strategies):
            self.play_player_turn(player, strategy)
            player_results.append(
                {
                    "bust": self.rules.is_bust(player.hand),
                    "blackjack": self.rules.is_blackjack(player.hand),
                }
            )
        # If all players busted or have blackjack, skip dealer turn
        if all(r["bust"] or r["blackjack"] for r in player_results):
            return
        self.play_dealer_turn()
