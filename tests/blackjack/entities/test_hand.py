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


def test_hand_str_and_repr():
    hand = Hand()
    assert str(hand) == "[]"
    assert "Hand([])" in repr(hand)
    hand.add_card(Card("A", "♠"))
    assert str(hand) == "[A♠]"
    assert "Hand([Card(rank='A', suit='♠')])" in repr(hand)
