from enum import Enum, auto


class Action(Enum):
    HIT = auto()
    STAND = auto()
    GAME_END = auto()
