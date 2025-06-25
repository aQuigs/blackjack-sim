import pytest

from blackjack.action import Action
from blackjack.entities.card import Card
from blackjack.entities.deck_schema import StandardBlackjackSchema
from blackjack.entities.hand import Hand
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.game import Game
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.base import Strategy
from blackjack.strategy.random import StandardDealerStrategy


class AlwaysStandStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return Action.STAND if Action.STAND in available_actions else available_actions[0]


class AlwaysHitStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return Action.HIT if Action.HIT in available_actions else available_actions[0]


def test_player_initialization():
    strategy = AlwaysStandStrategy()
    player = Player("Alice", strategy)
    assert player.name == "Alice"
    assert isinstance(player.hand, Hand)
    assert player.hand.cards == []
    assert player.strategy == strategy


def test_game_all_players_bust():
    # Force all players to bust by using AlwaysHitStrategy and a single deck
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    # Stack the deck so players get hands that can still hit and will bust
    # Deal order: P1, P2, D, P1, P2, D, then players hit
    shoe.cards = [
        ("10", "♠"),  # Player 2 hit (busts)
        ("10", "♥"),  # Player 1 hit (busts)
        ("5", "♣"),  # Dealer second card
        ("6", "♦"),  # Player 2 second card
        ("7", "♠"),  # Player 1 second card
        ("2", "♣"),  # Dealer first card
        ("4", "♥"),  # Player 2 first card
        ("3", "♦"),  # Player 1 first card
        # Add more cards to prevent running out
        ("9", "♠"),
        ("8", "♥"),
        ("7", "♦"),
        ("6", "♣"),
        ("5", "♠"),
        ("4", "♥"),
        ("3", "♦"),
        ("2", "♣"),
        ("A", "♠"),
        ("K", "♥"),
        ("Q", "♦"),
        ("J", "♣"),
    ]

    def deal_card_patch():
        rank, suit = shoe.cards.pop()
        return Card(rank, suit)

    shoe.deal_card = deal_card_patch
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [AlwaysHitStrategy(), AlwaysHitStrategy()]
    game = Game(player_strategies, shoe, rules, dealer_strategy)
    game.play_round()
    assert all(rules.is_bust(player.hand) or rules.hand_value(player.hand).value == 21 for player in game.players)
    # Dealer should not draw any additional cards after initial deal
    assert len(game.dealer.hand.cards) >= 2


def test_game_all_players_blackjack():
    # Force all players to get blackjack by stacking the shoe
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    # Correct stack for deal order: P1, P2, D, P1, P2, D
    shoe.cards = [
        ("3", "♣"),  # Dealer second card
        ("K", "♥"),  # Player 2 second card
        ("K", "♠"),  # Player 1 second card
        ("2", "♣"),  # Dealer first card
        ("A", "♥"),  # Player 2 first card
        ("A", "♠"),  # Player 1 first card
    ]

    def deal_card_patch():
        rank, suit = shoe.cards.pop()
        return Card(rank, suit)

    shoe.deal_card = deal_card_patch
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [AlwaysStandStrategy(), AlwaysStandStrategy()]
    game = Game(player_strategies, shoe, rules, dealer_strategy)
    game.play_round()
    assert all(rules.is_blackjack(player.hand) for player in game.players)
    # Dealer should not draw any additional cards after initial deal
    assert len(game.dealer.hand.cards) >= 2


def test_game_dealer_plays_if_needed():
    # One player stands on 12, dealer should play
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [AlwaysStandStrategy()]
    game = Game(player_strategies, shoe, rules, dealer_strategy)
    game.play_round()
    # Dealer should have more than 2 cards if they hit
    assert len(game.dealer.hand.cards) >= 2


def test_player_wins_when_dealer_busts(caplog):
    class StandStrategy(Strategy):
        def choose_action(self, hand, available_actions, game_state):
            return Action.STAND

    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    # Stack the shoe so player stands on 7, dealer busts with 22
    # Deal order: P, D, P, D, then dealer hits
    shoe.cards = [
        ("10", "♠"),  # Dealer hit (busts)
        ("J", "♠"),  # Dealer second card
        ("4", "♥"),  # Player second card
        ("2", "♦"),  # Dealer first card
        ("3", "♦"),  # Player first card
    ]

    def deal_card_patch():
        rank, suit = shoe.cards.pop()
        return Card(rank, suit)

    shoe.deal_card = deal_card_patch
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [StandStrategy()]
    game = Game(player_strategies, shoe, rules, dealer_strategy)

    with caplog.at_level("INFO"):
        game.play_round()
    # Player should not bust
    assert not rules.is_bust(game.players[0].hand)
    # Dealer should bust
    assert rules.is_bust(game.dealer.hand)
    # Check log for correct bust message
    assert any("Dealer busts with hand" in r for r in caplog.messages)


def test_player_str_and_repr():
    strategy = AlwaysStandStrategy()
    player = Player("TestPlayer", strategy)
    assert str(player) == "TestPlayer: []"
    assert "Player(name='TestPlayer', hand=Hand([]))" in repr(player)


def test_player_rejects_none_strategy():
    with pytest.raises(ValueError, match="Strategy cannot be None"):
        Player("TestPlayer", None)


def test_player_strategy_setter_accepts_valid_strategy():
    strategy1 = AlwaysStandStrategy()
    strategy2 = AlwaysHitStrategy()
    player = Player("TestPlayer", strategy1)
    assert player.strategy == strategy1
    player.strategy = strategy2
    assert player.strategy == strategy2


def test_hand_str_and_repr():
    hand = Hand()
    assert str(hand) == "[]"
    assert "Hand([])" in repr(hand)
    hand.add_card(Card("A", "♠"))
    assert str(hand) == "[A♠]"
    assert "Hand([Card(rank='A', suit='♠')])" in repr(hand)


def test_simulation_init_and_run():
    from blackjack.simulation import Simulation

    sim = Simulation(1)
    assert sim.num_games == 1
    assert sim.results == []
    assert sim.run() is None


def test_game_play_turn_invalid_action():
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [AlwaysHitStrategy()]
    game = Game(player_strategies, shoe, rules, dealer_strategy)

    class InvalidStrategy(Strategy):
        def choose_action(self, hand, available_actions, game_state):
            class FakeAction:
                name = "INVALID"

            return FakeAction()

    player = game.players[0]
    with pytest.raises(RuntimeError):
        game.play_turn(player, InvalidStrategy())


def test_game_no_available_actions():
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [AlwaysHitStrategy()]
    game = Game(player_strategies, shoe, rules, dealer_strategy)

    class NoActionStrategy(Strategy):
        def choose_action(self, hand, available_actions, game_state):
            return available_actions[0] if available_actions else None

    # Patch rules to return no actions
    rules.available_actions = lambda hand, gs: []
    player = game.players[0]
    # Should raise RuntimeError
    with pytest.raises(RuntimeError):
        game.play_turn(player, NoActionStrategy())


def test_game_all_players_bust_or_blackjack():
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [AlwaysHitStrategy(), AlwaysHitStrategy()]
    game = Game(player_strategies, shoe, rules, dealer_strategy)
    # Patch rules to force all players to bust or blackjack
    rules.is_bust = lambda hand: True
    rules.is_blackjack = lambda hand: False
    game.play_round()


def test_game_dealer_no_available_actions(caplog):
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [AlwaysHitStrategy()]
    game = Game(player_strategies, shoe, rules, dealer_strategy)
    # Patch rules to return no actions for dealer
    rules.available_actions = lambda hand, gs: []
    with pytest.raises(RuntimeError):
        game.play_turn(game.dealer, dealer_strategy)


def test_game_dealer_invalid_action_error():
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    dealer_strategy = StandardDealerStrategy()
    player_strategies = [AlwaysHitStrategy()]
    game = Game(player_strategies, shoe, rules, dealer_strategy)

    class InvalidStrategy(Strategy):
        def choose_action(self, hand, available_actions, game_state):
            class FakeAction:
                name = "INVALID"

            return FakeAction()

    with pytest.raises(RuntimeError):
        game.play_turn(game.dealer, InvalidStrategy())
