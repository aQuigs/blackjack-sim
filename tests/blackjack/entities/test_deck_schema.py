from app.src.blackjack.entities.deck_schema import StandardBlackjackSchema
from app.src.blackjack.entities.card import Card


def test_standard_blackjack_schema_counts():
    schema = StandardBlackjackSchema()
    counts = schema.card_counts()
    # 52 cards in a standard deck
    assert sum(counts.values()) == 52
    # Each card appears once
    for rank in Card.RANKS:
        for suit in Card.SUITS:
            assert counts[(rank, suit)] == 1
