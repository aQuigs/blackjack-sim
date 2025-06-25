import pytest

from blackjack.action import Action
from blackjack.entities.card import Card
from blackjack.entities.hand import Hand
from blackjack.entities.player import Player
from blackjack.game import Game
from blackjack.rules.standard import StandardBlackjackRules


def test_player_initialization(always_stand_strategy):
    player = Player("Alice", always_stand_strategy)
    assert player.name == "Alice"
    assert isinstance(player.hand, Hand)
    assert player.hand.cards == []
    assert player.strategy == always_stand_strategy


def test_game_all_players_bust(stacked_shoe, always_hit_strategy, standard_dealer_strategy):
    shoe = stacked_shoe(
        [
            ("10", "♠"),
            ("10", "♥"),
            ("5", "♣"),
            ("6", "♦"),
            ("7", "♠"),
            ("2", "♣"),
            ("4", "♥"),
            ("3", "♦"),
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
    )
    rules = GameTestRules()
    player_strategies = [always_hit_strategy, always_hit_strategy]
    game = Game(player_strategies, shoe, rules, standard_dealer_strategy)
    game.play_round()
    assert all(rules.is_bust(player.hand) or rules.hand_value(player.hand).value == 21 for player in game.players)
    assert len(game.dealer.hand.cards) >= 2


def test_game_all_players_blackjack(stacked_shoe, always_stand_strategy, standard_dealer_strategy):
    shoe = stacked_shoe(
        [
            ("3", "♣"),
            ("K", "♥"),
            ("K", "♠"),
            ("2", "♣"),
            ("A", "♥"),
            ("A", "♠"),
        ]
    )
    rules = GameTestRules()
    player_strategies = [always_stand_strategy, always_stand_strategy]
    game = Game(player_strategies, shoe, rules, standard_dealer_strategy)
    game.play_round()
    assert all(rules.is_blackjack(player.hand) for player in game.players)
    assert len(game.dealer.hand.cards) >= 2


def test_game_dealer_plays_if_needed(always_stand_strategy, standard_dealer_strategy):
    from blackjack.entities.deck_schema import StandardBlackjackSchema
    from blackjack.entities.shoe import Shoe
    from blackjack.rules.standard import StandardBlackjackRules

    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    player_strategies = [always_stand_strategy]
    game = Game(player_strategies, shoe, rules, standard_dealer_strategy)
    game.play_round()
    assert len(game.dealer.hand.cards) >= 2


def test_player_wins_when_dealer_busts(stacked_shoe, standard_dealer_strategy, caplog):
    class StandStrategy:
        def choose_action(self, hand, available_actions, game_state):
            return Action.STAND

    shoe = stacked_shoe(
        [
            ("10", "♠"),
            ("J", "♠"),
            ("4", "♥"),
            ("2", "♦"),
            ("3", "♦"),
        ]
    )
    rules = GameTestRules()
    player_strategies = [StandStrategy()]
    game = Game(player_strategies, shoe, rules, standard_dealer_strategy)
    with caplog.at_level("INFO"):
        game.play_round()
    assert not rules.is_bust(game.players[0].hand)
    assert rules.is_bust(game.dealer.hand)
    assert any("Dealer busts with hand" in r for r in caplog.messages)


def test_player_str_and_repr(always_stand_strategy):
    player = Player("TestPlayer", always_stand_strategy)
    assert str(player) == "TestPlayer: []"
    assert "Player(name='TestPlayer', hand=Hand([]))" in repr(player)


def test_player_rejects_none_strategy():
    with pytest.raises(ValueError, match="Strategy cannot be None"):
        Player("TestPlayer", None)


def test_player_strategy_setter_accepts_valid_strategy(always_stand_strategy, always_hit_strategy):
    player = Player("TestPlayer", always_stand_strategy)
    assert player.strategy == always_stand_strategy
    player.strategy = always_hit_strategy
    assert player.strategy == always_hit_strategy


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


def test_game_play_turn_invalid_action(always_hit_strategy, standard_dealer_strategy):
    from blackjack.entities.deck_schema import StandardBlackjackSchema
    from blackjack.entities.shoe import Shoe
    from blackjack.rules.standard import StandardBlackjackRules

    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    player_strategies = [always_hit_strategy]
    game = Game(player_strategies, shoe, rules, standard_dealer_strategy)

    class InvalidStrategy:
        def choose_action(self, hand, available_actions, game_state):
            class FakeAction:
                name = "INVALID"

            return FakeAction()

    player = game.players[0]
    with pytest.raises(RuntimeError):
        game.play_turn(player, InvalidStrategy())


def test_game_no_available_actions(always_hit_strategy, standard_dealer_strategy):
    from blackjack.entities.deck_schema import StandardBlackjackSchema
    from blackjack.entities.shoe import Shoe
    from blackjack.rules.standard import StandardBlackjackRules

    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    player_strategies = [always_hit_strategy]
    game = Game(player_strategies, shoe, rules, standard_dealer_strategy)

    class NoActionStrategy:
        def choose_action(self, hand, available_actions, game_state):
            return available_actions[0] if available_actions else None

    rules.available_actions = lambda hand, gs: []
    player = game.players[0]
    with pytest.raises(RuntimeError):
        game.play_turn(player, NoActionStrategy())


def test_game_all_players_bust_or_blackjack(always_hit_strategy, standard_dealer_strategy):
    from blackjack.entities.deck_schema import StandardBlackjackSchema
    from blackjack.entities.shoe import Shoe
    from blackjack.rules.standard import StandardBlackjackRules

    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    player_strategies = [always_hit_strategy, always_hit_strategy]
    game = Game(player_strategies, shoe, rules, standard_dealer_strategy)
    rules.is_bust = lambda hand: True
    rules.is_blackjack = lambda hand: False
    game.play_round()


def test_game_dealer_no_available_actions(always_hit_strategy, standard_dealer_strategy):
    from blackjack.entities.deck_schema import StandardBlackjackSchema
    from blackjack.entities.shoe import Shoe
    from blackjack.rules.standard import StandardBlackjackRules

    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    player_strategies = [always_hit_strategy]
    game = Game(player_strategies, shoe, rules, standard_dealer_strategy)
    rules.available_actions = lambda hand, gs: []
    with pytest.raises(RuntimeError):
        game.play_turn(game.dealer, standard_dealer_strategy)


def test_game_dealer_invalid_action_error(always_hit_strategy, standard_dealer_strategy):
    from blackjack.entities.deck_schema import StandardBlackjackSchema
    from blackjack.entities.shoe import Shoe
    from blackjack.rules.standard import StandardBlackjackRules

    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    player_strategies = [always_hit_strategy]
    game = Game(player_strategies, shoe, rules, standard_dealer_strategy)

    class InvalidStrategy:
        def choose_action(self, hand, available_actions, game_state):
            class FakeAction:
                name = "INVALID"

            return FakeAction()

    with pytest.raises(RuntimeError):
        game.play_turn(game.dealer, InvalidStrategy())


class GameTestRules(StandardBlackjackRules):
    # Inherit from StandardBlackjackRules if you need to override methods for tests
    pass
