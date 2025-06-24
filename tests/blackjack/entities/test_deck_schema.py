from blackjack.entities.card import Card
from blackjack.entities.deck_schema import StandardBlackjackSchema


def test_standard_blackjack_schema_counts():
    schema = StandardBlackjackSchema()
    counts = schema.card_counts()
    # 52 cards in a standard deck
    assert sum(counts.values()) == 52
    # Each card appears once
    for rank in Card.RANKS:
        for suit in Card.SUITS:
            assert counts[(rank, suit)] == 1


def test_standard_blackjack_schema_init_and_counts():
    schema = StandardBlackjackSchema()
    counts = schema.card_counts()
    assert isinstance(counts, dict)
    assert len(counts) == 52


def test_standard_blackjack_schema_card_counts_full():
    schema = StandardBlackjackSchema()
    counts = schema.card_counts()
    # Check that every card in a standard deck is present
    for rank in Card.RANKS:
        for suit in Card.SUITS:
            assert (rank, suit) in counts
            assert counts[(rank, suit)] == 1
