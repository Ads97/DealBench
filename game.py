import random
from typing import List, Optional, Dict, Any
from deck import Deck
from player import Player
from card import Card, MoneyCard, PropertyCard, WildPropertyCard, RentCard, CardType
from action import Action, ActionType
from rules_engine import RulesEngine
import random 
import sys
import json
from deck_config import INITIAL_HAND_SIZE, MAX_HAND_SIZE, ACTIONS_PER_TURN, DRAWS_PER_TURN

class Game:
    """Orchestrates the Monopoly Deal game flow."""

    def __init__(self, players: List[Player]):
        """
        Initializes the game with a list of players.

        Args:
            players: A list of Player objects participating in the game.
        """
        if not players or len(players) < 2 or len(players) > 5:
            raise ValueError("Game requires between 2 and 5 players.")

        print("Initializing Game...")
        # 1. Create and shuffle the deck
        self.deck: Deck = Deck() 
        print(f"Created deck with {self.deck.total_cards} cards.")
        random.shuffle(players)
        self.players = players
        print(f"Play order: {', '.join([p.name for p in players])}")

        # 4. Initialize Action Handler
        self.rules_engine = RulesEngine()

        # 5. Deal initial hands
        print(f"Dealing initial {INITIAL_HAND_SIZE} cards to each player...")
        for player in self.players:
            for _ in range(INITIAL_HAND_SIZE):
                card = self.deck.draw_card()
                player.add_card_to_hand(card)
        
        self.game_winner = None
        print("Initial hands dealt.")

        print("Game Setup Complete.")

    def run_game(self):
        """Runs the main game loop until a winner is determined."""
        print("\n--- Starting Game --- ")
        self.turn_count = 0
        while self.game_winner is None:
            current_player = self._get_current_player()
            print(f"\n--- {current_player.name}'s Turn ---")
            self._take_turn(current_player)
            has_won = self.rules_engine.check_win_condition(current_player)
            if has_won:
                self.game_winner = current_player.name
                print(f"\n--- GAME OVER --- {self.game_winner} wins! ---")
                break
            self.turn_count += 1

        if self.game_winner:
            print(f"{self.game_winner} is the winner after {self.turn_count} turns!")

    def _get_current_player(self):
        return self.players[self.turn_count%len(self.players)]
        
    def _take_turn(self, player: Player):
        """Handles the logic for a single player's turn."""
        print(f"{player.name} starts turn.")
        # print(json.dumps(self.to_json(debug=True), indent=4))
        # draw two cards first 
        for _ in range(DRAWS_PER_TURN):
            card = self.deck.draw_card()
            player.add_card_to_hand(card)
        
        # now play up to 3 actions
        self.actions_played = 0
        while self.actions_played < ACTIONS_PER_TURN:
            # TODO: Display game state to player (hand, properties, bank etc.)
            print(f"{player.name} has played {self.actions_played}/{ACTIONS_PER_TURN} actions.")

            # Get action from player
            action: Action = player.get_action(self.to_json())

            if action.action_type == ActionType.PASS: # Player chose to end turn
                print(f"{player.name} has chosen to end their action phase.")
                break

            # Validate and Execute Action
            if self.rules_engine.validate_action(action, player, self.actions_played):
                self.execute(action)
                if action.action_type != ActionType.MOVE_PROPERTY:
                    self.actions_played += 1 # Move property does not count as an action
                print(f"Action successful: {action}")
                # Check win condition immediately if action could cause win (e.g. placing last property)
                has_won = self.rules_engine.check_win_condition(player)
                if has_won:
                        self.game_winner = player
                        return # End turn immediately if someone won
            else:
                print("Invalid action chosen. Please try again.")
                sys.exit(1)
            # print(f"TEMP: Simulating action {actions_played}") # TEMP

        # 3. Discard excess cards
        while player.cards_in_hand > MAX_HAND_SIZE:
            num_cards_to_discard = player.cards_in_hand - MAX_HAND_SIZE
            print(f"{player.name} has more than {MAX_HAND_SIZE} cards! Discard {num_cards_to_discard} cards")
            cards_to_discard = player.choose_cards_to_discard(num_cards_to_discard, self.to_json())
            # TODO: Separate out the functions where a player chooses what to do, and the functions that control player state?
            for card in cards_to_discard:
                player.remove_card_from_hand(card)
            # Discard chosen cards into self.game_state.discard_pile

        print(f"{player.name} ends turn.")

    def to_json(self, debug=False) -> Dict[str, Any]:
        """Exposes all the game state that a player should have access to."""
        json_state = {
            "current_player_name": self._get_current_player().name,
            "turns_completed_in_game": self.turn_count,
            "actions_played_in_current_turn": self.actions_played,
            "players": [player.to_json(debug) for player in self.players],
        }
        return json_state

    def _get_player_by_name(self, name: str) -> Optional[Player]:
        """Finds the Player object corresponding to a name."""
        for player in self._get_all_players():
            if player.name == name:
                return player
        return None

    def _get_all_players(self) -> List[Player]:
        """Placeholder to get the list of Player objects."""
        return self.players 

    def execute(self, action: Action) -> None:
        """Handle playing an action card."""
        # Assuming Card object has a method like is_action() or check type
        # if not self.card.is_action(): 
        #     raise ValueError(f"Card {self.card.name} is not an action card.")

        # Remove card from player's hand and add to discard pile
        action.source_player.remove_card_from_hand(action.card)
        self.deck.discard_card(action.card) # Assuming game has discard_pile with add method

        action_type = action.action_type

        match action_type:
            case ActionType.ADD_TO_BANK:
                self._execute_add_to_bank(action)
            case ActionType.ADD_TO_PROPERTIES:
                self._execute_add_to_properties(action)
            case ActionType.MOVE_PROPERTY:
                self._execute_move_property(action)
            case ActionType.PASS:
                self._execute_pass(action)
            case ActionType.PLAY_ACTION:
                self._execute_action(action)
            case _:
                raise ValueError(f"Unexpected action type: {action_type}")

    def _execute_add_to_bank(self, action: Action):
        """Handle playing a money card to the bank."""
        player = action.source_player
        card = action.card
        
        player.add_card_to_bank(card)
        print(f"{player.name} banked ${card.value}M")

    def _execute_add_to_properties(self, action: Action):
        """Handle playing a standard property card to the table."""
        player = action.source_player
        card = action.card
        
        # Remove from hand and add to properties
        if isinstance(card, WildPropertyCard):
            card.current_color = action.target_property_set
        player.add_card_to_properties(card)
        print(f"{player.name} added property {card.name} to {action.target_property_set}")
    
    def _execute_move_property(self, action: Action):
        """Handle moving a property card to a different set."""
        player = action.source_player
        card = action.card
        target_property_set = action.target_property_set
        
        # Remove from hand and add to properties
        player.remove_card_from_properties(card)
        player.add_card_to_properties(card)
        print(f"{player.name} moved property {card.name} to {target_property_set}")

    def _execute_pass(self, action):
        raise ValueError("Pass action should not be executed.")

    def _execute_action(self, action):
        """Handle playing an action card."""
        match action.card.get_card_type():
            case CardType.ACTION_RENT:
                self._execute_action_rent(action)
            case _:
                raise ValueError(f"Unexpected action type: {action.card.get_card_type()}")
    
    def _execute_action_rent(self, action: Action): #TODO: handle double the rent
        """Handle playing a rent card."""
        player = action.source_player
        card = action.card
        property_sets = player.get_property_sets()
        rent_value = property_sets[action.rent_color].get_rent_value()
        if action.double_the_rent_count:
            rent_value = rent_value * 2**action.double_the_rent_count
        
        # Charge rent to other players
        if not card.is_wild:
            for other_player in self._get_all_players():
                if other_player != player:
                    payment_cards = other_player.provide_payment(reason="rent",amount=rent_value)
                    while not self.rules_engine.validate_rent_payment(payment_cards):
                        payment_cards = other_player.provide_payment(reason="rent",amount=rent_value)
                    print(f"{other_player.name} paid {rent_value}M to {player.name} with cards {payment_cards} for rent.")
                    for card, source in payment_cards:
                        player.add_card(card, source)
                        other_player.remove_card(card, source)
        else:
            target_player_name = action.target_player_names[0]
            target_player = self._get_player_by_name(target_player_name)
            if target_player is None:
                raise ValueError(f"Target player {target_player_name} not found.")
            payment_cards = target_player.provide_payment(reason="rent",amount=rent_value)
            while not self.rules_engine.validate_rent_payment(payment_cards):
                payment_cards = target_player.provide_payment(reason="rent",amount=rent_value)
            print(f"{target_player.name} paid {rent_value}M to {player.name} with cards {payment_cards} for rent.")
            for card, source in payment_cards:
                player.add_card(card, source)
                target_player.remove_card(card, source)

class TestPlayer(Player):
    def get_action(self, game_state_dict: dict) -> Optional[Action]:
        """
        Build a list of every *legal* move the player can make in the current
        state, then pick one uniformly at random.  
        Falls back to a PASS action if nothing is available.
        """
        valid_actions: list[Action] = []

        # Pre‑compute data that several cards may need
        property_sets         = self.get_property_sets()
        my_property_colors    = list(property_sets.keys())
        other_player_names    = [p["name"] for p in game_state_dict["players"] if p["name"] != self.name]
        double_the_rent_count = sum(
            1 for c in self.hand if getattr(c, "get_card_type", lambda: None)() == CardType.ACTION_DOUBLE_THE_RENT
        )
        double_the_rent_count = min(double_the_rent_count, ACTIONS_PER_TURN -game_state_dict['actions_played_in_current_turn'] - 1)

        for card in self.hand:

            # --- Money ----------------------------------------------------------
            if isinstance(card, MoneyCard):
                valid_actions.append(
                    Action(source_player=self, card=card,
                        action_type=ActionType.ADD_TO_BANK)
                )

            # --- Wild property --------------------------------------------------
            elif isinstance(card, WildPropertyCard):
                for color in card.available_colors:
                    valid_actions.append(
                        Action(source_player=self, card=card,
                            action_type=ActionType.ADD_TO_PROPERTIES,
                            target_property_set=color)
                    )

            # --- Standard property ---------------------------------------------
            elif isinstance(card, PropertyCard):
                valid_actions.append(
                    Action(source_player=self, card=card,
                        action_type=ActionType.ADD_TO_PROPERTIES)
                )
                valid_actions.append(
                    Action(source_player=self, card=card,
                        action_type=ActionType.ADD_TO_BANK)
                )

            # --- Rent card ------------------------------------------------------
            elif isinstance(card, RentCard) and my_property_colors:
                if not card.is_wild:
                    # Coloured rent card
                    for color in my_property_colors:
                        if color in card.colors:
                            valid_actions.append(
                                Action(source_player=self, card=card,
                                    action_type=ActionType.PLAY_ACTION,
                                    rent_color=color,
                                    double_the_rent_count=double_the_rent_count)
                            )
                else:
                    # Wild rent card: can pick any colour + any single opponent
                    for color in my_property_colors:
                        for target in other_player_names:
                            valid_actions.append(
                                Action(source_player=self, card=card,
                                    action_type=ActionType.PLAY_ACTION,
                                    rent_color=color,
                                    target_player_names=[target],
                                    double_the_rent_count=double_the_rent_count)
                            )

        # ------------------------------------------------------------------------
        # Choose and return one action (or PASS if none are legal)
        # ------------------------------------------------------------------------
        if valid_actions:
            return random.choice(valid_actions)

        # TODO: Test move property action
        return Action(source_player=self, action_type=ActionType.PASS)
    
    
    def choose_cards_to_discard(self, num_cards_to_discard, game_state_dict) -> List[Card]:
        cards_to_discard = random.sample(self.hand,num_cards_to_discard)
        return cards_to_discard
    
    def provide_payment(self, reason: str, amount: int):
        bank_value = sum(card.value for card in self.bank)
        if bank_value >= amount:
            payment = []
            total = 0
            sorted_bank = sorted(self.bank, key=lambda x: x.value)
            for card in sorted_bank:
                payment.append((card, "bank"))
                total += card.value
                if total >= amount:
                    return payment
        else:   
            payment = [(card, "bank") for card in self.bank.copy()]
            total = bank_value
            sorted_properties = sorted(self.property_sets.values(), key=lambda x: x.total_value())
            for prop_set in sorted_properties:
                for card in prop_set.cards:
                    payment.append((card, "properties"))
                    total += card.value
                    if total >= amount:
                        return payment
        return payment
        
        

class LLMPlayer(Player):
    def get_action(self, game_state_dict: dict) -> Action | None:
        return None

# Example Usage (Conceptual - requires other classes and deck_utils)
if __name__ == "__main__":
    players = [
        TestPlayer(name="Alice"),
        TestPlayer(name="Bob"),
        # Add AIPlayer later
    ]
    assert len(players) == len(set([player.name for player in players])), "Player names should be unique!"
    game = Game(players)
    game.run_game()
