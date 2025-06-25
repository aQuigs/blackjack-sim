class Simulation:
    def __init__(self, num_games: int) -> None:
        self.num_games: int = num_games
        self.results: list[dict[str, object]] = []

    def run(self) -> None:
        pass
