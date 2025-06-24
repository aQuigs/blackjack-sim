import pytest

from blackjack.entities.card import Card
from blackjack.entities.deck_schema import StandardBlackjackSchema
from blackjack.entities.shoe import Shoe


def test_shoe_initialization_and_cards_left():
    schema = StandardBlackjackSchema()
    shoe = Shoe(schema, num_decks=2)
    assert shoe.cards_left() == 104
    # All cards are Card instances
    assert all(isinstance(card, Card) for card in shoe.cards)


def test_shoe_shuffle_changes_order():
    schema = StandardBlackjackSchema()
    shoe = Shoe(schema)
    original_order = shoe.cards.copy()
    shoe.shuffle()
    # It's possible (but extremely unlikely) for the order to be the same
    assert shoe.cards != original_order or shoe.cards_left() != 52


def test_shoe_deal_card_and_depletion():
    schema = StandardBlackjackSchema()
    shoe = Shoe(schema, num_decks=1)
    dealt = [shoe.deal_card() for _ in range(52)]
    assert len(dealt) == 52
    assert shoe.cards_left() == 0
    with pytest.raises(ValueError):
        shoe.deal_card()


def test_shoe_cards_left():
    schema = StandardBlackjackSchema()
    shoe = Shoe(schema, num_decks=1)
    assert shoe.cards_left() == 52
    shoe.deal_card()
    assert shoe.cards_left() == 51
