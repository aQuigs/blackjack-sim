from app.src.deck.player import Player
from app.src.deck.shoe import Shoe
from app.src.deck.rules import Rules
from enum import Enum, auto
import logging


class Action(Enum):
    HIT = auto()
    STAND = auto()
    # Add more actions as needed (DOUBLE, SPLIT, etc.)


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
            # Defensive: ensure all actions are valid Action enums
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
                # Defensive: No valid action found
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
        # Future: determine outcomes, payouts, etc.

    # Future: implement game flow, dealing, actions, outcomes, etc.