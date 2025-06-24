from app.src.blackjack.entities.hand import Hand
from app.src.blackjack.entities.card import Card
from app.src.blackjack.entities.player import Player
from app.src.blackjack.entities.shoe import Shoe
from app.src.blackjack.entities.deck_schema import DeckSchema
from app.src.blackjack.rules.base import HandValue
from app.src.blackjack.rules.base import Rules
from app.src.blackjack.rules.standard import StandardBlackjackRules
from app.src.blackjack.strategy.base import PlayerStrategy
from app.src.blackjack.strategy.random import RandomStrategy
from app.src.blackjack.game import Action


class HandValue:
    def __init__(self, value: int, soft: bool):
        self.value = value
        self.soft = soft
    def __repr__(self):
        return f"HandValue(value={self.value}, soft={self.soft})"

class Rules:
    def hand_value(self, hand: Hand) -> HandValue:
        raise NotImplementedError
    def is_blackjack(self, hand: Hand) -> bool:
        raise NotImplementedError
    def is_bust(self, hand: Hand) -> bool:
        raise NotImplementedError
    def dealer_should_hit(self, hand: Hand) -> bool:
        raise NotImplementedError
    def blackjack_payout(self) -> float:
        raise NotImplementedError
    def available_actions(self, hand: Hand, game_state: dict) -> list[Action]:
        raise NotImplementedError
    def can_continue(self, hand: Hand, game_state: dict) -> bool:
        raise NotImplementedError
