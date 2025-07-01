from enum import Enum, auto


class Action(Enum):
    HIT = auto()
    STAND = auto()
    DOUBLE = auto()
    NOOP = auto()
