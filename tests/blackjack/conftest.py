import pytest

from blackjack.entities.card import Card
from blackjack.entities.deck_schema import StandardBlackjackSchema
from blackjack.entities.shoe import Shoe
from blackjack.game_events import GameEventType
from blackjack.rules.standard import StandardBlackjackRules
from blackjack.strategy.base import Strategy
from blackjack.strategy.strategy import StandardDealerStrategy


class AlwaysStandStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "STAND"), available_actions[0])


class AlwaysHitStrategy(Strategy):
    def choose_action(self, hand, available_actions, game_state):
        return next((a for a in available_actions if a.name == "HIT"), available_actions[0])


@pytest.fixture
def always_stand_strategy():
    return AlwaysStandStrategy()


@pytest.fixture
def always_hit_strategy():
    return AlwaysHitStrategy()


@pytest.fixture
def standard_dealer_strategy():
    return StandardDealerStrategy()


@pytest.fixture
def stacked_shoe():
    def _stacked_shoe(cards, num_decks=1):
        deck_schema = StandardBlackjackSchema()
        shoe = Shoe(deck_schema, num_decks=num_decks)
        shoe.cards = [Card(rank, suit) for rank, suit in cards]
        return shoe

    return _stacked_shoe


@pytest.fixture
def custom_rules():
    def _custom_rules(**overrides):
        class CustomRules(StandardBlackjackRules):
            pass

        for name, func in overrides.items():
            setattr(CustomRules, name, staticmethod(func))
        return CustomRules()

    return _custom_rules


def parse_final_hands_and_outcomes(event_log):
    hands = {}
    outcomes = {}
    for e in event_log:
        if e.event_type == GameEventType.ROUND_RESULT:
            hands[e.name] = e.hand
            if e.outcome is not None:
                outcomes[e.name] = e.outcome
    return hands, outcomes
