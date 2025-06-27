from blackjack.cli import BlackjackCLI
from blackjack.entities.card import Card
from blackjack.entities.state import Outcome
from blackjack.game_events import GameEventType
from blackjack.strategy.base import Strategy
from blackjack.strategy.strategy import StandardDealerStrategy
from tests.blackjack.conftest import parse_final_hands_and_outcomes


class AlwaysHitStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "HIT"), available_actions[0])


class AlwaysStandStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "STAND"), available_actions[0])


def test_game_all_players_bust():
    # Player 1: 10, 2, 8, 5 = 25 (bust after two hits)
    # Player 2: 10, 2, 8, 5 = 25 (bust after two hits)
    # Dealer: 6, 7
    shoe_cards = [
        Card("10", "♠"),  # P1 first
        Card("10", "♥"),  # P2 first
        Card("6", "♣"),  # D first
        Card("2", "♣"),  # P1 second
        Card("2", "♦"),  # P2 second
        Card("7", "♥"),  # D second
        Card("8", "♦"),  # P1 hit 1
        Card("5", "♣"),  # P1 hit 2 (bust)
        Card("8", "♠"),  # P2 hit 1
        Card("5", "♦"),  # P2 hit 2 (bust)
        Card("4", "♠"),  # Dealer extra
        Card("3", "♦"),  # Dealer extra
    ]
    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.run(num_players=2, printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player 1"] == Outcome.BUST
    assert outcomes["Player 2"] == Outcome.BUST
    assert hands["Player 1"] == [Card("10", "♠"), Card("2", "♣"), Card("8", "♦"), Card("5", "♣")]
    assert hands["Player 2"] == [Card("10", "♥"), Card("2", "♦"), Card("8", "♠"), Card("5", "♦")]
    assert hands["Dealer"] == [Card("6", "♣"), Card("7", "♥")]
    player1_actions = [
        e.action.name for e in event_log if getattr(e, "player", None) == "Player 1" and hasattr(e, "action")
    ]
    player2_actions = [
        e.action.name for e in event_log if getattr(e, "player", None) == "Player 2" and hasattr(e, "action")
    ]
    assert player1_actions == ["HIT", "HIT"]
    assert player2_actions == ["HIT", "HIT"]


def test_game_all_players_blackjack():
    # P1: A♠, K♠ (blackjack)
    # P2: A♥, K♥ (blackjack)
    # D: 9♣, 8♣
    shoe_cards = [
        Card("A", "♠"),
        Card("A", "♥"),
        Card("9", "♣"),
        Card("K", "♠"),
        Card("K", "♥"),
        Card("8", "♣"),
    ]
    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.run(num_players=2, printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player 1"] == Outcome.BLACKJACK
    assert outcomes["Player 2"] == Outcome.BLACKJACK
    assert hands["Player 1"] == [Card("A", "♠"), Card("K", "♠")]
    assert hands["Player 2"] == [Card("A", "♥"), Card("K", "♥")]
    assert hands["Dealer"] == [Card("9", "♣"), Card("8", "♣")]
    player1_events = [
        e for e in event_log if getattr(e, "player", None) == "Player 1" and e.event_type == GameEventType.BLACKJACK
    ]
    player2_events = [
        e for e in event_log if getattr(e, "player", None) == "Player 2" and e.event_type == GameEventType.BLACKJACK
    ]
    assert player1_events
    assert player2_events


def test_player_wins_when_dealer_busts():
    # P1: 10♠, Q♠ (20, stands)
    # D: 9♠, 5♣ (14), hits 2♦ (16), hits 8♣ (24, bust)
    shoe_cards = [
        Card("10", "♠"),  # P1 first
        Card("9", "♠"),  # D first
        Card("Q", "♠"),  # P1 second
        Card("5", "♣"),  # D second
        Card("2", "♦"),  # D hit 1
        Card("8", "♣"),  # D hit 2 (bust)
    ]
    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.run(num_players=1, printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player 1"] == Outcome.WIN
    assert hands["Player 1"] == [Card("10", "♠"), Card("Q", "♠")]
    assert hands["Dealer"] == [Card("9", "♠"), Card("5", "♣"), Card("2", "♦"), Card("8", "♣")]
    dealer_actions = [
        e.action.name for e in event_log if getattr(e, "player", None) == "Dealer" and hasattr(e, "action")
    ]
    assert dealer_actions == ["HIT", "HIT"]
    dealer_bust_events = [
        e for e in event_log if getattr(e, "player", None) == "Dealer" and e.event_type == GameEventType.BUST
    ]
    assert dealer_bust_events


def test_game_push():
    # P1: 10♠, Q♠ (20)
    # D: 10♣, Q♣ (20)
    shoe_cards = [
        Card("10", "♠"),
        Card("10", "♣"),
        Card("Q", "♠"),
        Card("Q", "♣"),
    ]
    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.run(num_players=1, printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player 1"] == Outcome.PUSH
    assert hands["Player 1"] == [Card("10", "♠"), Card("Q", "♠")]
    assert hands["Dealer"] == [Card("10", "♣"), Card("Q", "♣")]
    player_events = [e for e in event_log if getattr(e, "player", None) == "Player 1"]
    assert not any(e.event_type == GameEventType.BUST for e in player_events)
    assert not any(e.event_type == GameEventType.BLACKJACK for e in player_events)


def test_state_transition_graph_simple_game():
    """Test that the state transition graph contains expected transitions for a simple game."""
    from blackjack.action import Action
    from blackjack.entities.state import TerminalState

    shoe_cards = [
        Card("10", "♠"),  # Player first
        Card("9", "♣"),  # Dealer first
        Card("7", "♦"),  # Player second
        Card("8", "♣"),  # Dealer second
        Card("4", "♠"),  # Player hit
    ]
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )
    graph = cli.run(num_players=1, printable=False).get_graph()
    # There should be at least one transition from the initial state via HIT
    found = False
    for _state, actions in graph.items():
        for action, _next_states in actions.items():
            if action == Action.HIT:
                found = True
    assert found
    # There should be a GAME_END transition to a TerminalState
    found_terminal = False
    for _state, actions in graph.items():
        for action, next_states in actions.items():
            if action == Action.GAME_END:
                for next_state in next_states:
                    if isinstance(next_state, TerminalState):
                        found_terminal = True
    assert found_terminal


def test_normal_win_and_loss():
    # Player 1: 10♠, 9♠ (19)
    # Player 2: 8♠, 7♠ (15)
    # Dealer: 10♣, 8♣ (18)
    shoe_cards = [
        Card("10", "♠"),  # P1 first card
        Card("8", "♠"),  # P2 first card
        Card("10", "♣"),  # Dealer first card
        Card("9", "♠"),  # P1 second card
        Card("7", "♠"),  # P2 second card
        Card("8", "♣"),  # Dealer second card
    ]
    event_log = []
    cli = BlackjackCLI.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.run(num_players=2, printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player 1"] == Outcome.WIN
    assert outcomes["Player 2"] == Outcome.LOSE
    assert hands["Player 1"] == [Card("10", "♠"), Card("9", "♠")]
    assert hands["Player 2"] == [Card("8", "♠"), Card("7", "♠")]
    assert hands["Dealer"] == [Card("10", "♣"), Card("8", "♣")]
