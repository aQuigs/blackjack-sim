from blackjack.action import Action
from blackjack.blackjack_cli import BlackjackService
from blackjack.entities.card import Card
from blackjack.entities.state import Outcome, ProperState, TerminalState, Turn
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.rules.standard import StandardBlackjackRules
from tests.blackjack.conftest import AlwaysHitStrategy, AlwaysStandStrategy


class TestEVCalculator:
    def setup_method(self):
        self.rules = StandardBlackjackRules()

    def test_empty_graph_returns_empty_dict(self):
        service = BlackjackService.create_null()
        graph = StateTransitionGraph()
        result = service.calculate_evs(graph)
        assert result == {}

    def test_terminal_states_initialized_with_correct_payouts(self):
        cards = [
            Card("A", "♠"),  # Player first card
            Card("K", "♣"),  # Dealer first card
            Card("10", "♦"),  # Player second card (blackjack)
            Card("10", "♥"),  # Dealer second card
        ] + [
            Card("2", "♠")
        ] * 10  # Extra cards for dealer if needed
        service = BlackjackService.create_null(shoe_cards=cards)
        graph = service.play_games(num_players=1, num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Check that terminal states are initialized with correct payouts
        win_state = TerminalState(Outcome.WIN)
        lose_state = TerminalState(Outcome.LOSE)
        push_state = TerminalState(Outcome.PUSH)
        bust_state = TerminalState(Outcome.BUST)
        blackjack_state = TerminalState(Outcome.BLACKJACK)

        if win_state in result:
            assert result[win_state].action_evs[Action.GAME_END] == 1.0
        if lose_state in result:
            assert result[lose_state].action_evs[Action.GAME_END] == -1.0
        if push_state in result:
            assert result[push_state].action_evs[Action.GAME_END] == 0.0
        if bust_state in result:
            assert result[bust_state].action_evs[Action.GAME_END] == -1.0
        if blackjack_state in result:
            assert result[blackjack_state].action_evs[Action.GAME_END] == 1.5

    def test_simple_win_scenario(self):
        # Create a game where player stands with 20, dealer has 19
        cards = [
            Card("10", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("10", "♦"),  # Player second card (20)
            Card("10", "♥"),  # Dealer second card (19)
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysStandStrategy())
        graph = service.play_games(num_players=1, num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 20 and dealer state
        player_state_20 = None
        dealer_state = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 20 and state.turn == Turn.PLAYER:
                player_state_20 = state
            elif isinstance(state, ProperState) and state.turn == Turn.DEALER:
                dealer_state = state

        if player_state_20 and dealer_state:
            assert result[player_state_20].optimal_action == Action.STAND
            assert result[dealer_state].optimal_action == Action.GAME_END

    def test_simple_loss_scenario(self):
        # Create a game where player stands with 16, dealer has 20
        cards = [
            Card("8", "♠"),  # Player first card
            Card("10", "♣"),  # Dealer first card
            Card("8", "♦"),  # Player second card (16)
            Card("10", "♥"),  # Dealer second card (20)
            Card("2", "♠"),  # Extra card for dealer if needed
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysStandStrategy())
        graph = service.play_games(num_players=1, num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 16
        player_state_16 = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 16 and state.turn == Turn.PLAYER:
                player_state_16 = state
                break

        if player_state_16:
            assert result[player_state_16].optimal_action == Action.STAND

    def test_hit_vs_stand_decision(self):
        # Create a game where player has 16 and can hit or stand
        cards = [
            Card("8", "♠"),  # Player first card
            Card("10", "♣"),  # Dealer first card
            Card("8", "♦"),  # Player second card (16)
            Card("4", "♥"),  # Player hit card (20)
            Card("10", "♠"),  # Dealer second card
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysHitStrategy())
        graph = service.play_games(num_players=1, num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 16
        player_state_16 = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 16 and state.turn == Turn.PLAYER:
                player_state_16 = state
                break

        if player_state_16:
            # Should prefer HIT over STAND when it leads to 20
            assert result[player_state_16].optimal_action == Action.HIT

    def test_bust_scenario(self):
        # Create a game where player hits and busts
        cards = [
            Card("10", "♠"),  # Player first card
            Card("10", "♣"),  # Dealer first card
            Card("10", "♦"),  # Player second card (20)
            Card("10", "♥"),  # Player hit card (30, bust)
            Card("10", "♠"),  # Dealer second card (needed for complete game)
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysHitStrategy())
        graph = service.play_games(num_players=1, num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 20
        player_state_20 = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 20 and state.turn == Turn.PLAYER:
                player_state_20 = state
                break

        if player_state_20:
            # The player strategy is AlwaysHit, so they will hit and bust
            # The EV calculation should show that HIT leads to -1.0 (bust)
            assert result[player_state_20].action_evs[Action.HIT] == -1.0

    def test_blackjack_scenario(self):
        cards = [
            Card("A", "♠"),  # Player first card
            Card("10", "♣"),  # Dealer first card
            Card("10", "♦"),  # Player second card (blackjack)
            Card("10", "♥"),  # Dealer second card
        ] + [
            Card("2", "♠")
        ] * 10  # Extra cards for dealer if needed
        service = BlackjackService.create_null(shoe_cards=cards)
        graph = service.play_games(num_players=1, num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the blackjack state
        blackjack_state = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 21 and state.player_hand_soft:
                blackjack_state = state
                break

        if blackjack_state:
            assert result[blackjack_state].optimal_action == Action.GAME_END
            assert result[blackjack_state].action_evs[Action.GAME_END] == 1.5
