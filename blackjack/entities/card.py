class Card:
    SUITS: list[str] = ["♥", "♦", "♣", "♠"]
    RANKS: list[str] = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    TEN_RANKS: set[str] = {"10", "J", "Q", "K"}

    def __init__(self, rank: str, suit: str) -> None:
        if rank not in Card.RANKS:
            raise ValueError(f"Invalid rank: {rank}")

        if suit not in Card.SUITS:
            raise ValueError(f"Invalid suit: {suit}")

        self.rank: str = rank
        self.suit: str = suit

    def is_ace(self) -> bool:
        return self.rank == "A"

    @property
    def rank_value(self) -> int:
        if self.rank in Card.TEN_RANKS:
            return 10
        elif self.is_ace():
            return 11
        else:
            return int(self.rank)

    @property
    def graph_rank(self) -> str:
        return "10" if self.rank in Card.TEN_RANKS else self.rank

    def is_ten(self) -> bool:
        return self.rank in Card.TEN_RANKS

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return f"Card(rank='{self.rank}', suit='{self.suit}')"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented

        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self):
        return hash((self.rank, self.suit))
