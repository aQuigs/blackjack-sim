from blackjack.entities.card import Card
from blackjack.entities.hand import Hand


def test_hand_initial():
    hand = Hand()
    assert hand.cards == []


def test_hand_add_card():
    hand = Hand()
    card = Card("5", "♣")
    hand.add_card(card)
    assert hand.cards == [card]
    card2 = Card("A", "♠")
    hand.add_card(card2)
    assert hand.cards == [card, card2]
