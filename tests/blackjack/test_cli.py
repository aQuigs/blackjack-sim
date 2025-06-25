from click.testing import CliRunner

from blackjack.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Run a blackjack simulation from the command line." in result.output


def test_cli_default_run():
    runner = CliRunner()
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "Player 1 final hand:" in result.output
    assert "Dealer final hand:" in result.output
    assert "Result:" in result.output


def test_cli_multiple_players_and_decks():
    runner = CliRunner()
    result = runner.invoke(main, ["--num-players", "2", "--num-decks", "2"])
    assert result.exit_code == 0
    assert "Player 1 final hand:" in result.output
    assert "Player 2 final hand:" in result.output
    assert "Dealer final hand:" in result.output
    assert "Result:" in result.output


def test_cli_no_print():
    runner = CliRunner()
    result = runner.invoke(main, ["--no-print"])
    assert result.exit_code == 0
    # Should not print hands or result
    assert "Player 1 final hand:" not in result.output
    assert "Dealer final hand:" not in result.output
    assert "Result:" not in result.output
