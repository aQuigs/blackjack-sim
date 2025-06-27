import concurrent.futures
import logging
from typing import Optional

import click

from blackjack.entities.deck_schema import StandardBlackjackSchema
from blackjack.entities.random_wrapper import RandomWrapper
from blackjack.entities.shoe import Shoe
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.game import Game
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.strategy import RandomStrategy, StandardDealerStrategy


def print_state_transition_graph(graph: StateTransitionGraph) -> None:
    for state, actions in graph.get_graph().items():
        print(f"  {state}:")
        for action, next_states in actions.items():
            for next_state, count in next_states.items():
                print(f"    --{action.name}--> {next_state} [count={count}]")


class BlackjackCLI:
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

    def run(
        self, num_players: int, num_rounds: int = 1, shuffle_between_rounds: bool = True, printable: bool = True
    ) -> StateTransitionGraph:
        logging.basicConfig(level=logging.ERROR, format="%(message)s")

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


def run_batch(
    num_decks: int,
    num_players: int,
    num_rounds: int,
    shuffle_between_rounds: bool,
) -> StateTransitionGraph:
    cli = BlackjackCLI(num_decks=num_decks)

    return cli.run(
        num_players=num_players,
        num_rounds=num_rounds,
        shuffle_between_rounds=shuffle_between_rounds,
        printable=False,
    )


def run_parallel_batches(
    num_decks: int,
    num_players: int,
    num_rounds: int,
    no_shuffle_between: bool,
    no_print: bool,
    parallel: int,
) -> StateTransitionGraph:
    if parallel == 1 or num_rounds == 1:
        return run_batch(num_decks, num_players, num_rounds, not no_shuffle_between)

    base_batch = num_rounds // parallel
    remainder = num_rounds % parallel
    batch_sizes = [base_batch + (1 if i < remainder else 0) for i in range(parallel)]

    args_list = [
        (num_decks, num_players, batch_size, not no_shuffle_between)
        for batch_size in batch_sizes
    ]

    with concurrent.futures.ProcessPoolExecutor(max_workers=parallel) as executor:
        graphs = list(executor.map(lambda args: run_batch(*args), args_list))

    main_graph = graphs[0]
    for g in graphs[1:]:
        main_graph.merge(g)
    return main_graph


@click.command()
@click.option("--num-players", default=1, show_default=True, type=click.IntRange(1, 5), help="Number of players (1-5).")
@click.option("--num-decks", default=1, show_default=True, type=click.IntRange(1, 8), help="Number of decks (1-8).")
@click.option(
    "--num-rounds",
    default=1,
    show_default=True,
    type=click.IntRange(1, 1000000000),
    help="Number of rounds to play (1-1000000000).",
)
@click.option("--no-shuffle-between", is_flag=True, help="Don't shuffle the shoe between rounds.")
@click.option("--no-print", is_flag=True, help="Disable printing of hands and results.")
@click.option(
    "--parallel",
    default=1,
    show_default=True,
    type=click.IntRange(1, 128),
    help="Number of parallel batches to run.",
)
def main(num_players, num_decks, num_rounds, no_shuffle_between, no_print, parallel):
    """Run a blackjack simulation from the command line."""
    try:
        main_graph = run_parallel_batches(
            num_decks=num_decks,
            num_players=num_players,
            num_rounds=num_rounds,
            no_shuffle_between=no_shuffle_between,
            no_print=no_print,
            parallel=parallel,
        )

        if not no_print:
            print_state_transition_graph(main_graph)

    except Exception as exc:
        logging.error(f"Error running blackjack simulation: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
