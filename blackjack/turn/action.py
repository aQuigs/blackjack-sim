from enum import Enum, auto


class Action(Enum):
    HIT = auto()
    STAND = auto()
    DOUBLE = auto()
    SPLIT = auto()
    NOOP = auto()
