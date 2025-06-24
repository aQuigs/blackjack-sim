from app.src.blackjack.entities.player import Player
from app.src.blackjack.entities.hand import Hand


def test_player_initialization():
    player = Player("Alice")
    assert player.name == "Alice"
    assert isinstance(player.hand, Hand)
    assert player.hand.cards == []
