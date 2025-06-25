from blackjack.cli import BlackjackCLI
from blackjack.entities.card import Card
from blackjack.game_events import PlayerOutcome, Winner
from blackjack.strategy.base import Strategy
from blackjack.strategy.random import StandardDealerStrategy


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
    result = cli.run(num_players=2, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.BUST
    assert result.player_results[1].outcome == PlayerOutcome.BUST
    assert result.player_results[0].hand == [Card("10", "♠"), Card("2", "♣"), Card("8", "♦"), Card("5", "♣")]
    assert result.player_results[1].hand == [Card("10", "♥"), Card("2", "♦"), Card("8", "♠"), Card("5", "♦")]
    assert result.dealer_hand == [Card("6", "♣"), Card("7", "♥")]
    player1_actions = [
        e.payload.action.name
        for e in event_log
        if getattr(e.payload, "player", None) == "Player 1" and hasattr(e.payload, "action")
    ]
    player2_actions = [
        e.payload.action.name
        for e in event_log
        if getattr(e.payload, "player", None) == "Player 2" and hasattr(e.payload, "action")
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
    result = cli.run(num_players=2, printable=False)
    for player_result in result.player_results:
        assert player_result.outcome == PlayerOutcome.BLACKJACK
    assert result.player_results[0].hand == [Card("A", "♠"), Card("K", "♠")]
    assert result.player_results[1].hand == [Card("A", "♥"), Card("K", "♥")]
    assert result.dealer_hand == [Card("9", "♣"), Card("8", "♣")]
    player1_events = [
        e for e in event_log if getattr(e.payload, "player", None) == "Player 1" and e.type.name == "BLACKJACK"
    ]
    player2_events = [
        e for e in event_log if getattr(e.payload, "player", None) == "Player 2" and e.type.name == "BLACKJACK"
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
    result = cli.run(num_players=1, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.ACTIVE
    assert result.winner == Winner.PLAYER
    assert result.player_results[0].hand == [Card("10", "♠"), Card("Q", "♠")]
    assert result.dealer_hand == [Card("9", "♠"), Card("5", "♣"), Card("2", "♦"), Card("8", "♣")]
    dealer_actions = [
        e.payload.action.name
        for e in event_log
        if getattr(e.payload, "player", None) == "Dealer" and hasattr(e.payload, "action")
    ]
    assert dealer_actions == ["HIT", "HIT"]
    dealer_bust_events = [
        e for e in event_log if getattr(e.payload, "player", None) == "Dealer" and e.type.name == "BUST"
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
    result = cli.run(num_players=1, printable=False)
    assert result.player_results[0].outcome == PlayerOutcome.ACTIVE
    assert result.winner == Winner.PUSH
    assert result.player_results[0].hand == [Card("10", "♠"), Card("Q", "♠")]
    assert result.dealer_hand == [Card("10", "♣"), Card("Q", "♣")]
    player_events = [e for e in event_log if getattr(e.payload, "player", None) == "Player 1"]
    assert not any(e.type.name == "BUST" for e in player_events)
    assert not any(e.type.name == "BLACKJACK" for e in player_events)
