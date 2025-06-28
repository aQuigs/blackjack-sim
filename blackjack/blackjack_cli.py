from typing import Optional

from blackjack.entities.deck_schema import StandardBlackjackSchema
from blackjack.entities.random_wrapper import RandomWrapper
from blackjack.entities.shoe import Shoe
from blackjack.entities.state import State
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.ev_calculator import EVCalculator, StateEV
from blackjack.game import Game
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.strategy import RandomStrategy, StandardDealerStrategy


def print_state_transition_graph(graph: StateTransitionGraph) -> None:
    for state, actions in graph.get_graph().items():
        print(f"  {state}:")
        for action, next_states in actions.items():
            for next_state, count in next_states.items():
                print(f"    --{action.name}--> {next_state} [count={count}]")


class BlackjackService:
    def __init__(
        self,
        num_decks=1,
        output_tracker=None,
        deck_schema=None,
        rules=None,
        player_strategy=None,
        dealer_strategy=None,
        shoe: Optional[Shoe] = None,
    ):
        self.output_tracker = output_tracker
        self.deck_schema = deck_schema or StandardBlackjackSchema()
        self.rules = rules or StandardBlackjackRules()
        self.player_strategy = player_strategy or RandomStrategy()
        self.dealer_strategy = dealer_strategy or StandardDealerStrategy()
        self.shoe = shoe or Shoe(self.deck_schema, num_decks)
        self.num_decks = num_decks

    @classmethod
    def create_null(
        cls,
        num_decks=1,
        output_tracker=None,
        deck_schema=None,
        rules=None,
        player_strategy=None,
        dealer_strategy=None,
        shoe_cards=None,
        choice_responses=None,
    ):
        deck_schema = deck_schema or StandardBlackjackSchema()
        shoe = Shoe.create_null(deck_schema, num_decks, cards=shoe_cards)

        if player_strategy is None:
            random_wrapper = RandomWrapper(null=True, shuffle_response=shoe_cards, choice_responses=choice_responses)
            player_strategy = RandomStrategy(random_wrapper=random_wrapper)

        if dealer_strategy is None:
            dealer_strategy = StandardDealerStrategy()

        return cls(
            num_decks=num_decks,
            output_tracker=output_tracker,
            deck_schema=deck_schema,
            rules=rules,
            player_strategy=player_strategy,
            dealer_strategy=dealer_strategy,
            shoe=shoe,
        )

    def play_games(
        self, num_players: int, num_rounds: int = 1, shuffle_between_rounds: bool = True, printable: bool = True
    ) -> StateTransitionGraph:
        graph = StateTransitionGraph()

        for round_num in range(1, num_rounds + 1):
            if printable and num_rounds > 1:
                print(f"\n=== Round {round_num} ===")

            player_strategies = [self.player_strategy for _ in range(num_players)]

            game = Game(
                player_strategies,
                self.shoe,
                self.rules,
                self.dealer_strategy,
                output_tracker=self.output_tracker,
                state_transition_graph=graph,
            )

            game.play_round()

            if printable:
                print_state_transition_graph(graph)

            if shuffle_between_rounds and round_num < num_rounds:
                self.shoe.shuffle()
                if printable:
                    print(f"Shuffled shoe. Cards remaining: {self.shoe.cards_left()}")

        if printable and num_rounds > 1:
            print("\n=== Summary ===")
            print(f"Total rounds played: {num_rounds}")

        return graph

    def calculate_evs(self, graph: StateTransitionGraph) -> dict[State, StateEV]:
        calculator = EVCalculator(self.rules)
        return calculator.calculate_evs(graph)
