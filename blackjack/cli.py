import concurrent.futures
import cProfile
import logging
import pstats

import click

from blackjack.blackjack_cli import BlackjackService, print_state_transition_graph
from blackjack.entities.state_transition_graph import StateTransitionGraph


def print_ev_results(state_evs):
    """Print the EV calculation results in a readable format."""
    print("\n=== Expected Value Analysis ===")

    for state, state_ev in state_evs.items():
        print(f"\nState: {state}")
        print(f"  Optimal Action: {state_ev.optimal_action.name}")
        print("  Action EVs:")
        for action, ev in state_ev.action_evs.items():
            print(f"    {action.name}: {ev:.4f}")


def run_batch(
    num_decks: int,
    num_players: int,
    num_rounds: int,
    shuffle_between_rounds: bool,
    printable: bool = True,
) -> StateTransitionGraph:
    cli = BlackjackService(num_decks=num_decks)

    return cli.play_games(
        num_players=num_players,
        num_rounds=num_rounds,
        shuffle_between_rounds=shuffle_between_rounds,
        printable=printable,
    )


def run_batch_with_args(args):
    return run_batch(*args)


def run_parallel_batches(
    num_decks: int,
    num_players: int,
    num_rounds: int,
    no_shuffle_between: bool,
    no_print: bool,
    parallel: int,
) -> StateTransitionGraph:
    if parallel == 1 or num_rounds == 1:
        return run_batch(num_decks, num_players, num_rounds, not no_shuffle_between, not no_print)

    base_batch = num_rounds // parallel
    remainder = num_rounds % parallel
    batch_sizes = [base_batch + (1 if i < remainder else 0) for i in range(parallel)]

    args_list = [(num_decks, num_players, batch_size, not no_shuffle_between, False) for batch_size in batch_sizes]

    with concurrent.futures.ProcessPoolExecutor(max_workers=parallel) as executor:
        graphs = list(executor.map(run_batch_with_args, args_list))

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
@click.option(
    "--profile",
    is_flag=True,
    help="Enable profiling and save results to profile_results.prof.",
)
def main(num_players, num_decks, num_rounds, no_shuffle_between, no_print, parallel, profile):
    """Run a blackjack simulation from the command line."""
    logging.basicConfig(level=logging.ERROR if no_print else logging.DEBUG, format="%(message)s")

    if profile and parallel > 1:
        logging.error("Profiling is not supported with parallel processing (parallel > 1)")
        raise SystemExit(1)

    try:
        if profile:
            profiler = cProfile.Profile()
            profiler.enable()

        try:
            main_graph = run_parallel_batches(
                num_decks=num_decks,
                num_players=num_players,
                num_rounds=num_rounds,
                no_shuffle_between=no_shuffle_between,
                no_print=no_print,
                parallel=parallel,
            )
        finally:
            if profile:
                profiler.disable()

        if profile:
            stats = pstats.Stats(profiler)
            stats.sort_stats("cumulative")

            stats.dump_stats("profile_results.prof")
            print("Profile data saved to: profile_results.prof")

        if not no_print:
            print_state_transition_graph(main_graph)

    except Exception as exc:
        logging.error(f"Error running blackjack simulation: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
