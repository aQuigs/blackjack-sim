from app.src.blackjack.entities.hand import Hand
from app.src.blackjack.entities.card import Card


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
