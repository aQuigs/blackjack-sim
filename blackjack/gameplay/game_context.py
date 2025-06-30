

from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.rules.base import Rules


class GameContext:
    def __init__(
        self,
        players: list[Player],
        shoe: Shoe,
        rules: Rules,
        dealer: Player,
    ):
        self.players = players
        self.shoe = shoe
        self.rules = rules
        self.dealer = dealer
        self.is_player_turn = True
