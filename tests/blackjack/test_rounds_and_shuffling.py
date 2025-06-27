from blackjack.action import Action
from blackjack.cli import BlackjackCLI
from blackjack.entities.card import Card

# Fixed shoe: alternating player and dealer cards for deterministic results
# 1st round: Player1: 2♥, 3♥; Dealer: 4♥, 5♥; 2nd round: Player1: 6♥, 7♥; Dealer: 8♥, 9♥, etc.
FIXED_SHOE = [
    Card("2", "♥"),
    Card("4", "♥"),  # Player1, Dealer
    Card("3", "♥"),
    Card("5", "♥"),  # Player1, Dealer
    Card("6", "♥"),
    Card("8", "♥"),  # Player1, Dealer
    Card("7", "♥"),
    Card("9", "♥"),  # Player1, Dealer
    Card("10", "♥"),
    Card("J", "♥"),  # Player1, Dealer
    Card("Q", "♥"),
    Card("K", "♥"),  # Player1, Dealer
]


def test_multiple_rounds_with_shuffling():
    cli = BlackjackCLI.create_null(shoe_cards=list(FIXED_SHOE))
    results = cli.run(1, num_rounds=2, shuffle_between_rounds=True, printable=False)
    # With shuffling, the shoe is reset each round, so the first round is always the same
    # Since the strategy is random, we only check that the hands are the same for both rounds
    hand1 = results[0].player_results[0].hand
    hand2 = results[1].player_results[0].hand
    dealer1 = results[0].dealer_hand
    dealer2 = results[1].dealer_hand
    assert hand1 == hand2
    assert dealer1 == dealer2


def test_multiple_rounds_without_shuffling():
    # Configure the RandomStrategy to always choose HIT (first action in available_actions)
    choice_responses = [Action.HIT, Action.HIT]  # Player will hit twice in first round, twice in second round
    cli = BlackjackCLI.create_null(shoe_cards=list(FIXED_SHOE), choice_responses=choice_responses)
    results = cli.run(1, num_rounds=2, shuffle_between_rounds=False, printable=False)
    # Without shuffling, the shoe is depleted, so the hands should be different
    hand1 = results[0].player_results[0].hand
    hand2 = results[1].player_results[0].hand
    dealer1 = results[0].dealer_hand
    dealer2 = results[1].dealer_hand
    assert hand1 != hand2
    assert dealer1 != dealer2
    # The second round should use the next cards in the shoe
    assert hand2 == [Card("7", "♥"), Card("6", "♥"), Card("3", "♥"), Card("4", "♥"), Card("2", "♥")]
    assert dealer2 == [Card("8", "♥"), Card("5", "♥")]
