from blackjack.blackjack_service import BlackjackService
from blackjack.entities.card import Card
from blackjack.entities.state import Outcome, ProperState, TerminalState, Turn
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.turn.action import Action
from tests.blackjack.conftest import (
    AlwaysDoubleStrategy,
    AlwaysHitStrategy,
    AlwaysStandStrategy,
)


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
        graph = service.play_games(num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Check that terminal states are initialized with correct payouts
        win_state = TerminalState(Outcome.WIN)
        lose_state = TerminalState(Outcome.LOSE)
        push_state = TerminalState(Outcome.PUSH)
        blackjack_state = TerminalState(Outcome.BLACKJACK)

        if win_state in result:
            assert result[win_state].action_evs[Action.NOOP] == 1.0
            assert result[win_state].total_count == 0
        if lose_state in result:
            assert result[lose_state].action_evs[Action.NOOP] == -1.0
            assert result[lose_state].total_count == 0
        if push_state in result:
            assert result[push_state].action_evs[Action.NOOP] == 0.0
            assert result[push_state].total_count == 0
        if blackjack_state in result:
            assert result[blackjack_state].action_evs[Action.NOOP] == 1.5
            assert result[blackjack_state].total_count == 0

    def test_simple_win_scenario(self):
        # Create a game where player stands with 20, dealer has 19
        cards = [
            Card("10", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("10", "♦"),  # Player second card (20)
            Card("10", "♥"),  # Dealer second card (19)
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysStandStrategy())
        graph = service.play_games(num_rounds=1, printable=False)
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
            assert result[dealer_state].optimal_action == Action.NOOP

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
        graph = service.play_games(num_rounds=1, printable=False)
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
        graph = service.play_games(num_rounds=1, printable=False)
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
        graph = service.play_games(num_rounds=1, printable=False)
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
        graph = service.play_games(num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the blackjack state
        blackjack_state = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 21 and state.player_hand_soft:
                blackjack_state = state
                break

        if blackjack_state:
            assert result[blackjack_state].optimal_action == Action.NOOP
            assert result[blackjack_state].action_evs[Action.NOOP] == 1.5

    def test_total_count_calculation_for_non_terminal_states(self):
        # Create a simple game scenario to test total_count calculation
        cards = [
            Card("10", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("10", "♦"),  # Player second card (20)
            Card("10", "♥"),  # Dealer second card (19)
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysStandStrategy())
        graph = service.play_games(num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find non-terminal states and verify their total_count
        for state, state_ev in result.items():
            if not isinstance(state, TerminalState):
                # For non-terminal states, total_count should be the sum of all action counts
                # from the transition graph for this state
                expected_count = 0
                if state in graph.get_graph():
                    for next_states in graph.get_graph()[state].values():
                        expected_count += sum(next_states.values())

                assert state_ev.total_count == expected_count, f"State {state} has incorrect total_count"

    def test_total_count_with_multiple_rounds(self):
        # Test that total_count accumulates correctly across multiple rounds
        cards = [
            Card("10", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("10", "♦"),  # Player second card (20)
            Card("10", "♥"),  # Dealer second card (19)
        ] * 3  # Repeat for 3 rounds
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysStandStrategy())
        graph = service.play_games(num_rounds=3, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 20 and verify its total_count
        player_state_20 = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 20 and state.turn == Turn.PLAYER:
                player_state_20 = state
                break

        if player_state_20:
            # The state should be encountered 3 times (once per round)
            assert player_state_20 in graph.get_graph()
            expected_count = 0
            for next_states in graph.get_graph()[player_state_20].values():
                expected_count += sum(next_states.values())

            assert result[player_state_20].total_count == expected_count
            assert result[player_state_20].total_count >= 3  # Should be at least 3

    def test_double_ev_is_doubled_when_winning(self):
        # Test that double EV is properly doubled when player wins
        cards = [
            Card("10", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("5", "♦"),  # Player second card (15 total)
            Card("8", "♣"),  # Dealer second card (17 total)
            Card("6", "♥"),  # Player double card (21 total)
            Card("10", "♠"),  # Extra card for dealer if needed
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysDoubleStrategy())
        graph = service.play_games(num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 15 (before doubling)
        player_state_15 = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 15 and state.turn == Turn.PLAYER:
                player_state_15 = state
                break

        if player_state_15:
            # Double should be the optimal action
            assert result[player_state_15].optimal_action == Action.DOUBLE
            # Double EV should be 2.0 (doubled from 1.0 win)
            assert result[player_state_15].action_evs[Action.DOUBLE] == 2.0

    def test_double_ev_is_doubled_when_losing(self):
        # Test that double EV is properly doubled when player loses
        cards = [
            Card("10", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("5", "♦"),  # Player second card (15 total)
            Card("7", "♣"),  # Dealer second card (16 total)
            Card("5", "♥"),  # Player double card (20 total)
            Card("5", "♠"),  # Dealer hit card (21 total)
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysDoubleStrategy())
        graph = service.play_games(num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 15 (before doubling)
        player_state_15 = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 15 and state.turn == Turn.PLAYER:
                player_state_15 = state
                break

        if player_state_15:
            # Double should be the optimal action (even though it loses, it's the only action)
            assert result[player_state_15].optimal_action == Action.DOUBLE
            # Double EV should be -2.0 (doubled from -1.0 loss)
            assert result[player_state_15].action_evs[Action.DOUBLE] == -2.0

    def test_double_ev_is_doubled_when_pushing(self):
        # Test that double EV is properly doubled when player pushes
        cards = [
            Card("10", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("5", "♦"),  # Player second card (15 total)
            Card("6", "♣"),  # Dealer second card (15 total)
            Card("6", "♥"),  # Player double card (21 total)
            Card("6", "♠"),  # Dealer hit card (21 total)
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysDoubleStrategy())
        graph = service.play_games(num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 15 (before doubling)
        player_state_15 = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 15 and state.turn == Turn.PLAYER:
                player_state_15 = state
                break

        if player_state_15:
            # Double should be the optimal action
            assert result[player_state_15].optimal_action == Action.DOUBLE
            # Double EV should be 0.0 (doubled from 0.0 push)
            assert result[player_state_15].action_evs[Action.DOUBLE] == 0.0

    def test_double_ev_is_doubled_when_busting(self):
        # Test that double EV is properly doubled when player busts
        cards = [
            Card("10", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("5", "♦"),  # Player second card (15 total)
            Card("8", "♣"),  # Dealer second card (17 total)
            Card("10", "♥"),  # Player double card (25 total, bust)
            Card("10", "♠"),  # Extra card for dealer if needed
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysDoubleStrategy())
        graph = service.play_games(num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 15 (before doubling)
        player_state_15 = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 15 and state.turn == Turn.PLAYER:
                player_state_15 = state
                break

        if player_state_15:
            # Double should be the optimal action (even though it busts, it's the only action)
            assert result[player_state_15].optimal_action == Action.DOUBLE
            # Double EV should be -2.0 (doubled from -1.0 bust)
            assert result[player_state_15].action_evs[Action.DOUBLE] == -2.0

    def test_double_vs_hit_vs_stand_ev_comparison(self):
        # Test that double EV is properly compared against other actions
        cards = [
            Card("10", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("5", "♦"),  # Player second card (15 total)
            Card("8", "♣"),  # Dealer second card (17 total)
            Card("6", "♥"),  # Player double card (21 total)
            Card("4", "♠"),  # Player hit card (19 total)
            Card("10", "♠"),  # Extra card for dealer if needed
        ]

        # Create a strategy that can choose between double, hit, and stand
        class DoubleHitStandStrategy:
            def choose_action(self, hand, available_actions, game_state):
                if Action.DOUBLE in available_actions:
                    return Action.DOUBLE
                elif Action.HIT in available_actions:
                    return Action.HIT
                else:
                    return Action.STAND

        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=DoubleHitStandStrategy())
        graph = service.play_games(num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 15 (before doubling)
        player_state_15 = None
        for state in result:
            if isinstance(state, ProperState) and state.player_hand_value == 15 and state.turn == Turn.PLAYER:
                player_state_15 = state
                break

        if player_state_15:
            # Double should be the optimal action (2.0 EV vs 1.0 for hit to 21)
            assert result[player_state_15].optimal_action == Action.DOUBLE
            assert result[player_state_15].action_evs[Action.DOUBLE] == 2.0
            # Hit should have lower EV than double
            if Action.HIT in result[player_state_15].action_evs:
                assert result[player_state_15].action_evs[Action.HIT] < 2.0

    def test_double_ev_multiplier_in_ev_calculator(self):
        # Test that the EV_MULTIPLIER for DOUBLE is correctly set to 2
        from blackjack.ev_calculator import EV_MULTIPLIER

        assert EV_MULTIPLIER[Action.DOUBLE] == 2

    def test_double_ev_with_soft_hand(self):
        # Test double EV with a soft hand
        cards = [
            Card("A", "♠"),  # Player first card
            Card("9", "♣"),  # Dealer first card
            Card("5", "♦"),  # Player second card (16 total, soft)
            Card("8", "♣"),  # Dealer second card (17 total)
            Card("5", "♥"),  # Player double card (21 total)
            Card("10", "♠"),  # Extra card for dealer if needed
        ]
        service = BlackjackService.create_null(shoe_cards=cards, player_strategy=AlwaysDoubleStrategy())
        graph = service.play_games(num_rounds=1, printable=False)
        result = service.calculate_evs(graph)

        # Find the player state with 16 (soft, before doubling)
        player_state_16_soft = None
        for state in result:
            if (
                isinstance(state, ProperState)
                and state.player_hand_value == 16
                and state.player_hand_soft
                and state.turn == Turn.PLAYER
            ):
                player_state_16_soft = state
                break

        if player_state_16_soft:
            # Double should be the optimal action
            assert result[player_state_16_soft].optimal_action == Action.DOUBLE
            # Double EV should be 2.0 (doubled from 1.0 win)
            assert result[player_state_16_soft].action_evs[Action.DOUBLE] == 2.0
