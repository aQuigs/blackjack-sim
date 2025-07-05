import concurrent.futures
import cProfile
import logging
import pickle
import pstats
from typing import Optional

import click

from blackjack.blackjack_service import BlackjackService, print_state_transition_graph
from blackjack.entities.state import GraphState, Turn
from blackjack.entities.state_transition_graph import StateTransitionGraph
from blackjack.ev_calculator import StateEV
from blackjack.turn.action import Action


def print_ev_results(state_evs: dict[GraphState, StateEV]) -> None:
    """Print the EV calculation results in a readable format."""
    print("\n=== Expected Value Analysis ===")

    for state, state_ev in state_evs.items():
        if hasattr(state, "turn") and (state.turn != Turn.PLAYER or state_ev.optimal_action == Action.NOOP):
            continue

        print(f"\nState: {state}")
        print(f"  Optimal Action: {state_ev.optimal_action.name}")
        print(f"  Total Count: {state_ev.total_count}")
        print("  Action EVs:")
        for action, ev in state_ev.action_evs.items():
            print(f"    {action.name}: {ev:.8f}")


def run_batch(
    num_decks: int,
    num_rounds: int,
    shuffle_between_rounds: bool,
    printable: bool = True,
) -> StateTransitionGraph:
    cli = BlackjackService(num_decks=num_decks)

    return cli.play_games(
        num_rounds=num_rounds,
        shuffle_between_rounds=shuffle_between_rounds,
        printable=printable,
    )


def run_batch_with_args(args):
    return run_batch(*args)


def run_parallel_batches(
    num_decks: int,
    num_rounds: int,
    no_shuffle_between: bool,
    no_print: bool,
    parallel: int,
    main_graph: StateTransitionGraph,
) -> None:
    if parallel == 1 or num_rounds == 1:
        graph = run_batch(num_decks, num_rounds, not no_shuffle_between, not no_print)
        main_graph.merge(graph)
        return

    base_batch = num_rounds // parallel
    remainder = num_rounds % parallel
    batch_sizes = [base_batch + (1 if i < remainder else 0) for i in range(parallel)]

    args_list = [(num_decks, batch_size, not no_shuffle_between, False) for batch_size in batch_sizes]

    with concurrent.futures.ProcessPoolExecutor(max_workers=parallel) as executor:
        graphs = list(executor.map(run_batch_with_args, args_list))

    for g in graphs:
        main_graph.merge(g)


def import_graph(input_file: Optional[str]) -> StateTransitionGraph:
    if not input_file:
        return StateTransitionGraph()

    with open(input_file, "rb") as f:
        return pickle.load(f)


def export_graph(graph: StateTransitionGraph, output_file: Optional[str]) -> None:
    if not output_file:
        return

    with open(output_file, "wb") as f:
        return pickle.dump(graph, f)


@click.command()
@click.option("--num-decks", default=1, show_default=True, type=click.IntRange(1, 8), help="Number of decks (1-8).")
@click.option(
    "--num-rounds",
    default=1,
    show_default=True,
    type=click.IntRange(0, 1000000000),
    help="Number of rounds to play (0-1000000000).",
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
@click.option(
    "--graph-output-file",
    default=None,
    help="File to write the graph to",
)
@click.option(
    "--graph-input-file",
    default=None,
    help="File to read the starting graph from",
)
def main(
    num_decks, num_rounds, no_shuffle_between, no_print, parallel, profile, graph_output_file, graph_input_file
) -> None:
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
            main_graph: StateTransitionGraph = import_graph(graph_input_file)
            if not no_print:
                print("--START INITIAL GRAPH--")
                print_state_transition_graph(main_graph)
                print("--END INITIAL GRAPH--")

            run_parallel_batches(
                num_decks=num_decks,
                num_rounds=num_rounds,
                no_shuffle_between=no_shuffle_between,
                no_print=no_print,
                parallel=parallel,
                main_graph=main_graph,
            )
        finally:
            if profile:
                profiler.disable()

        if profile:
            stats = pstats.Stats(profiler)
            stats.sort_stats("cumulative")

            stats.dump_stats("profile_results.prof")
            print("Profile data saved to: profile_results.prof")

        export_graph(main_graph, graph_output_file)

        if not no_print:
            print_state_transition_graph(main_graph)

        # Calculate and print EV analysis
        if not no_print:
            try:
                cli = BlackjackService(num_decks=num_decks)
                state_evs = cli.calculate_evs(main_graph)
                print_ev_results(state_evs)
            except Exception as exc:
                logging.error(f"Error calculating EV analysis: {exc}")

    except Exception as exc:
        logging.error(f"Error running blackjack simulation: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
