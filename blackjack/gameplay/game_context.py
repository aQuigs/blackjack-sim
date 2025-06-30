

from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.rules.base import Rules


class GameContext:
    def __init__(
        self,
        player: Player,
        shoe: Shoe,
        rules: Rules,
        dealer: Player,
    ) -> None:
        self.player: Player = player
        self.shoe: Shoe = shoe
        self.rules: Rules = rules
        self.dealer: Player = dealer
        self.is_player_turn: bool = True
