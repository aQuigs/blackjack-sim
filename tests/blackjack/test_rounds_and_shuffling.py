from blackjack.action import Action
from blackjack.cli import BlackjackCLI
from blackjack.entities.card import Card
from tests.blackjack.conftest import parse_final_hands_and_outcomes

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
    event_logs = []
    cli = BlackjackCLI.create_null(shoe_cards=list(FIXED_SHOE), output_tracker=lambda e: event_logs.append([e]))
    cli.run(1, num_rounds=2, shuffle_between_rounds=True, printable=False)
    for event_log in event_logs:
        hands, outcomes = parse_final_hands_and_outcomes(event_log)
        if hands:
            assert ("Player 1" in hands) or ("Dealer" in hands)


def test_multiple_rounds_without_shuffling():
    event_logs = []
    cli = BlackjackCLI.create_null(
        shoe_cards=list(FIXED_SHOE),
        choice_responses=[Action.HIT, Action.HIT],
        output_tracker=lambda e: event_logs.append([e]),
    )
    cli.run(1, num_rounds=2, shuffle_between_rounds=False, printable=False)
    for event_log in event_logs:
        hands, outcomes = parse_final_hands_and_outcomes(event_log)
        if hands:
            assert ("Player 1" in hands) or ("Dealer" in hands)
