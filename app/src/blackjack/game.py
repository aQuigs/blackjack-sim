from app.src.blackjack.entities.player import Player
from app.src.blackjack.entities.shoe import Shoe
from app.src.blackjack.rules.base import Rules
from app.src.blackjack.action import Action
import logging


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

    def play_player_turn(self, player: Player):
        while True:
            if self.rules.is_bust(player.hand):
                break
            actions = self.rules.available_actions(player.hand, {})
            for action in actions:
                if not isinstance(action, Action):
                    raise ValueError(f"Invalid action type: {action}")
            if Action.HIT in actions:
                try:
                    player.hand.add_card(self.shoe.deal_card())
                except ValueError as e:
                    logging.error(f"Error dealing to player {player.name}: {e}")
                    break
            elif Action.STAND in actions:
                break
            else:
                logging.critical(
                    f"No valid action available for player {player.name} with hand {player.hand.cards}. "
                    f"Available actions: {actions}"
                )
                raise RuntimeError(
                    f"No valid action available for player {player.name} with hand {player.hand.cards}. "
                    f"Available actions: {actions}"
                )

    def play_dealer_turn(self):
        while self.rules.dealer_should_hit(self.dealer.hand):
            try:
                self.dealer.hand.add_card(self.shoe.deal_card())
            except ValueError as e:
                logging.error(f"Error dealing to dealer: {e}")
                break

    def play_round(self):
        self.initial_deal()
        for player in self.players:
            self.play_player_turn(player)
        self.play_dealer_turn()
