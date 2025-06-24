from app.src.blackjack.entities.deck_schema import StandardBlackjackSchema
from app.src.blackjack.entities.shoe import Shoe
from app.src.blackjack.rules.standard import StandardBlackjackRules
from app.src.blackjack.game import Game
from app.src.blackjack.action import Action
from app.src.blackjack.strategy.random import RandomStrategy


def main(printable: bool = True):
    num_players = 1
    num_decks = 1
    deck_schema = StandardBlackjackSchema()
    shoe = Shoe(deck_schema, num_decks)
    rules = StandardBlackjackRules()
    strategy = RandomStrategy()
    game = Game(num_players, shoe, rules)

    # Initial deal
    game.initial_deal()
    if printable:
        for i, player in enumerate(game.players):
            hand_str = " ".join(str(card) for card in player.hand.cards)
            print(f"Player {i+1} initial hand: {hand_str}")
        dealer_hand_str = " ".join(str(card) for card in game.dealer.hand.cards)
        print(f"Dealer initial hand: {dealer_hand_str}")

    # Player turns
    for i, player in enumerate(game.players):
        while True:
            if rules.is_bust(player.hand):
                if printable:
                    hand_str = " ".join(str(card) for card in player.hand.cards)
                    print(f"Player {i+1} busts with {hand_str}")
                break
            actions = rules.available_actions(player.hand, {})
            if not actions:
                break
            action = strategy.choose_action(player.hand, actions, {})
            if printable:
                print(f"Player {i+1} chooses {action.name}")
            if action == Action.HIT:
                card = shoe.deal_card()
                player.hand.add_card(card)
                if printable:
                    print(f"Player {i+1} draws {card}")
            elif action == Action.STAND:
                if printable:
                    hand_str = " ".join(str(card) for card in player.hand.cards)
                    print(f"Player {i+1} stands with {hand_str}")
                break
            else:
                print(f"Unknown action: {action}")
                break

    # Dealer turn
    if printable:
        dealer_hand_str = " ".join(str(card) for card in game.dealer.hand.cards)
        print(f"Dealer reveals hand: {dealer_hand_str}")
    while rules.dealer_should_hit(game.dealer.hand):
        card = shoe.deal_card()
        game.dealer.hand.add_card(card)
        if printable:
            print(f"Dealer draws {card}")
    if printable:
        dealer_hand_str = " ".join(str(card) for card in game.dealer.hand.cards)
        print(f"Dealer final hand: {dealer_hand_str}")

    # Results (basic)
    player_value = rules.hand_value(game.players[0].hand).value
    dealer_value = rules.hand_value(game.dealer.hand).value
    if rules.is_bust(game.players[0].hand):
        result = "Player busts, dealer wins."
    elif rules.is_bust(game.dealer.hand):
        result = "Dealer busts, player wins!"
    elif player_value > dealer_value:
        result = "Player wins!"
    elif player_value < dealer_value:
        result = "Dealer wins."
    else:
        result = "Push (tie)."
    if printable:
        print(f"Result: {result}")


if __name__ == "__main__":
    main(printable=True)
