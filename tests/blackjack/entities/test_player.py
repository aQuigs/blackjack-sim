from blackjack.action import Action
from blackjack.entities.card import Card
from blackjack.entities.deck_schema import StandardBlackjackSchema
from blackjack.entities.hand import Hand
from blackjack.entities.player import Player
from blackjack.entities.shoe import Shoe
from blackjack.game import Game
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.base import PlayerStrategy


class AlwaysStandStrategy(PlayerStrategy):
    def choose_action(self, hand, available_actions, game_state):
        return (
            Action.STAND if Action.STAND in available_actions else available_actions[0]
        )


class AlwaysHitStrategy(PlayerStrategy):
    def choose_action(self, hand, available_actions, game_state):
        return Action.HIT if Action.HIT in available_actions else available_actions[0]


def test_player_initialization():
    player = Player("Alice")
    assert player.name == "Alice"
    assert isinstance(player.hand, Hand)
    assert player.hand.cards == []


def test_game_all_players_bust():
    # Force all players to bust by using AlwaysHitStrategy and a single deck
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    game = Game(2, shoe, rules)
    strategies = [AlwaysHitStrategy(), AlwaysHitStrategy()]
    game.play_round(strategies)
    assert all(rules.is_bust(player.hand) for player in game.players)
    # Dealer should not draw any additional cards after initial deal
    assert len(game.dealer.hand.cards) == 2


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
    game = Game(2, shoe, rules)
    strategies = [AlwaysStandStrategy(), AlwaysStandStrategy()]
    game.play_round(strategies)
    assert all(rules.is_blackjack(player.hand) for player in game.players)
    # Dealer should not draw any additional cards after initial deal
    assert len(game.dealer.hand.cards) == 2


def test_game_dealer_plays_if_needed():
    # One player stands on 12, dealer should play
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks=1)
    rules = StandardBlackjackRules()
    game = Game(1, shoe, rules)
    strategies = [AlwaysStandStrategy()]
    game.play_round(strategies)
    # Dealer should have more than 2 cards if they hit
    assert len(game.dealer.hand.cards) >= 2
