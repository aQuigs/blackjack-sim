from enum import Enum, auto


class Action(Enum):
    HIT = auto()
    STAND = auto()
    NOOP = auto()
