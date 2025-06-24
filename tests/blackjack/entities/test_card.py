import pytest
from app.src.blackjack.entities.card import Card


def test_card_valid():
    card = Card("A", "♠")
    assert card.rank == "A"
    assert card.suit == "♠"
    assert str(card) == "A of ♠"
    assert repr(card) == "Card(rank='A', suit='♠')"


def test_card_invalid_rank():
    with pytest.raises(ValueError):
        Card("1", "♠")


def test_card_invalid_suit():
    with pytest.raises(ValueError):
        Card("A", "X")
