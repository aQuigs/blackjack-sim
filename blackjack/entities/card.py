class Card:
    SUITS: list[str] = ["♥", "♦", "♣", "♠"]
    RANKS: list[str] = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    def __init__(self, rank: str, suit: str) -> None:
        if rank not in Card.RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in Card.SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        self.rank: str = rank
        self.suit: str = suit

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return f"Card(rank='{self.rank}', suit='{self.suit}')"
