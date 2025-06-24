from blackjack.entities.hand import Hand
from blackjack.entities.player import Player


def test_player_initialization():
    player = Player("Alice")
    assert player.name == "Alice"
    assert isinstance(player.hand, Hand)
    assert player.hand.cards == []
