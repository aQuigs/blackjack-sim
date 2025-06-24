import pytest

from blackjack.entities.card import Card


def test_card_valid():
    card = Card("A", "♠")
    assert card.rank == "A"
    assert card.suit == "♠"
    assert str(card) == "A♠"
    assert repr(card) == "Card(rank='A', suit='♠')"


def test_card_invalid_rank():
    with pytest.raises(ValueError):
        Card("1", "♠")


def test_card_invalid_suit():
    with pytest.raises(ValueError):
        Card("A", "X")


def test_card_str_and_repr():
    card = Card("A", "♠")
    assert str(card) == "A♠"
    assert "Card(rank='A', suit='♠')" in repr(card)
