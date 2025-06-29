from blackjack.cli import BlackjackService
from blackjack.entities.card import Card
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.game import Game
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.strategy import StandardDealerStrategy
from blackjack.turn.action import Action
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
    cli = BlackjackService.create_null(shoe_cards=list(FIXED_SHOE), output_tracker=lambda e: event_logs.append([e]))
    cli.play_games(1, num_rounds=2, shuffle_between_rounds=True, printable=False)
    for event_log in event_logs:
        hands, outcomes = parse_final_hands_and_outcomes(event_log)
        if hands:
            assert ("Player 1" in hands) or ("Dealer" in hands)


def test_multiple_rounds_without_shuffling():
    event_logs = []
    cli = BlackjackService.create_null(
        shoe_cards=list(FIXED_SHOE),
        choice_responses=[Action.HIT, Action.HIT],
        output_tracker=lambda e: event_logs.append([e]),
    )
    cli.play_games(1, num_rounds=2, shuffle_between_rounds=False, printable=False)
    for event_log in event_logs:
        hands, outcomes = parse_final_hands_and_outcomes(event_log)
        if hands:
            assert ("Player 1" in hands) or ("Dealer" in hands)


def test_face_cards_shown_as_tens_in_graph(stacked_shoe, always_stand_strategy):
    cards = [
        ("7", "♠"),  # Extra card for player or dealer
        ("6", "♠"),  # Extra card for player or dealer
        ("4", "♠"),  # Extra card for player or dealer
        ("5", "♥"),  # Dealer hole card
        ("3", "♥"),  # Player 1 second card
        ("J", "♥"),  # Dealer upcard (face card)
        ("2", "♥"),  # Player 1 first card
    ]

    shoe = stacked_shoe(cards)
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    state_graph = StateTransitionGraph()

    game = Game(
        player_strategies=[always_stand_strategy],
        shoe=shoe,
        rules=rules,
        dealer_strategy=dealer_strategy,
        state_transition_graph=state_graph,
    )

    game.play_round()

    found = False
    for state, _actions in state_graph.transitions.items():
        if hasattr(state, "dealer_upcard_rank") and state.dealer_upcard_rank == "10":
            found = True
            break
    assert found
