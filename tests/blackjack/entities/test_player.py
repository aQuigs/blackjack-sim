from blackjack.cli import BlackjackService
from blackjack.entities.card import Card
from blackjack.entities.state import Outcome
from blackjack.game_events import GameEventType
from blackjack.strategy.base import Strategy
from blackjack.strategy.strategy import StandardDealerStrategy
from blackjack.turn.action import Action
from tests.blackjack.conftest import parse_final_hands_and_outcomes


class AlwaysHitStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "HIT"), available_actions[0])


class AlwaysStandStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "STAND"), available_actions[0])


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
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.WIN
    assert hands["Player"] == [Card("10", "♠"), Card("Q", "♠")]
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
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] == Outcome.PUSH
    assert hands["Player"] == [Card("10", "♠"), Card("Q", "♠")]
    assert hands["Dealer"] == [Card("10", "♣"), Card("Q", "♣")]
    player_events = [e for e in event_log if getattr(e, "player", None) == "Player"]
    assert not any(e.event_type == GameEventType.BUST for e in player_events)
    assert not any(e.event_type == GameEventType.BLACKJACK for e in player_events)


def test_state_transition_graph_simple_game():
    """Test that the state transition graph contains expected transitions for a simple game."""
    from blackjack.entities.state import TerminalState

    shoe_cards = [
        Card("10", "♠"),  # Player first
        Card("9", "♣"),  # Dealer first
        Card("7", "♦"),  # Player second
        Card("8", "♣"),  # Dealer second
        Card("4", "♠"),  # Player hit
    ]
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysHitStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
    )
    graph = cli.play_games(printable=False).get_graph()
    # There should be at least one transition from the initial state via HIT
    found = False
    for _state, actions in graph.items():
        for action, _next_states in actions.items():
            if action == Action.HIT:
                found = True
    assert found
    # There should be a NOOP transition to a TerminalState
    found_terminal = False
    for _state, actions in graph.items():
        for action, next_states in actions.items():
            if action == Action.NOOP:
                for next_state in next_states:
                    if isinstance(next_state, TerminalState):
                        found_terminal = True
    assert found_terminal


def test_normal_win_and_loss():
    # Player: 10♠, 10♣ (20)
    # Dealer: 9♠, 8♣ (17)
    shoe_cards = [
        Card("10", "♠"),  # Player first card
        Card("9", "♠"),  # Dealer first card
        Card("10", "♣"),  # Player second card
        Card("8", "♣"),  # Dealer second card
    ]
    event_log = []
    cli = BlackjackService.create_null(
        num_decks=1,
        player_strategy=AlwaysStandStrategy(),
        dealer_strategy=StandardDealerStrategy(),
        shoe_cards=list(reversed(shoe_cards)),
        output_tracker=event_log.append,
    )
    cli.play_games(printable=False)
    hands, outcomes = parse_final_hands_and_outcomes(event_log)
    assert outcomes["Player"] in (Outcome.WIN, Outcome.PUSH, Outcome.LOSE)
    assert hands["Player"] == [Card("10", "♠"), Card("10", "♣")]
    assert hands["Dealer"] == [Card("9", "♠"), Card("8", "♣")]


def test_state_transition_graph_merge():
    from blackjack.entities.state import PreDealState, ProperState
    from blackjack.entities.state_transition_graph import StateTransitionGraph

    g1 = StateTransitionGraph()
    g2 = StateTransitionGraph()
    s1 = PreDealState()
    s2 = ProperState(10, False, "A", 0, 0)
    s3 = ProperState(12, True, "K", 1, 0)
    g1.add_transition(s1, Action.HIT, s2)
    g1.add_transition(s2, Action.STAND, s3)
    g2.add_transition(s1, Action.HIT, s2)
    g2.add_transition(s2, Action.STAND, s3)
    g2.add_transition(s2, Action.HIT, s3)
    g1.merge(g2)
    graph = g1.get_graph()
    assert graph[s1][Action.HIT][s2] == 2
    assert graph[s2][Action.STAND][s3] == 2
    assert graph[s2][Action.HIT][s3] == 1
