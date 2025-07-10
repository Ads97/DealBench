from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

from card import Card, MoneyCard, PropertySet, PropertyColor, PropertyCard, WildPropertyCard, CardType
from action import ActionPropertyInfo, Action
import logging
logger = logging.getLogger(__name__)

class Player(ABC): # Inherit from ABC
    """Abstract Base Class for a player in the game."""
    def __init__(self, name: str):
        """Initializes a player with a name."""
        if not name or not isinstance(name, str):
            raise ValueError("Player name must be a non-empty string.")
        self.name = name
        self.hand: List[Card] = []  # Assuming Card objects will be defined later
        self.bank: List[Card] = []  # Stores MoneyCards and ActionCards banked
        self.property_sets: Dict[PropertyColor, PropertySet] = {}

    def add_card_to_hand(self, card):
        """Adds a card to the player's hand."""
        self.hand.append(card)

    def add_card(self, card, source):
        if source=="bank":
            self.add_card_to_bank(card)
        elif source=="hand":
            self.add_card_to_hand(card)
        elif source=="properties":
            self.add_card_to_properties(card)
        else:
            raise ValueError("Invalid source. Must be 'bank', 'hand', or 'properties'.")
    
    def remove_card(self, card, source):
        if source=="bank":
            self.remove_card_from_bank(card)
        elif source=="hand":
            self.remove_card_from_hand(card)
        elif source=="properties":
            self.remove_card_from_properties(card)
        else:
            raise ValueError("Invalid source. Must be 'bank', 'hand', or 'properties'.")

    def remove_card_from_hand(self, card):
        """Removes a specific card from the player's hand."""
        self.hand.remove(card)
    
    def remove_double_rent_card_from_hand(self):
        for card in self.hand:
            if card.get_card_type() == CardType.ACTION_DOUBLE_THE_RENT:
                self.hand.remove(card)
                return
        raise ValueError("No double the rent card found in hand.")

    def add_card_to_bank(self, card):
        """Adds a card (Money or Action) to the player's bank."""
        self.bank.append(card)

    def remove_card_from_bank(self, card):
        """Removes a specific card from the player's bank."""
        try:
            self.bank.remove(card)
        except ValueError:
            logger.error(f"Error: Card {card} not found in bank.") # Or raise a custom exception

    def add_card_to_properties(self, card, color=None):
        if color is None:
            if isinstance(card, WildPropertyCard):
                color = card.current_color
            elif isinstance(card, PropertyCard):
                color = card.set_color
            else:
                raise ValueError(f"add_card_to_properties: Error: color is None for card {card}")
        elif isinstance(card, WildPropertyCard):
            card.current_color = color

        if color not in self.property_sets:
            self.property_sets[color] = PropertySet(card)
        else:
            self.property_sets[color].add_card(card)

    def remove_card_from_properties(self, card):
        if isinstance(card, WildPropertyCard):
            color = card.current_color
        elif isinstance(card, PropertyCard):
            color = card.set_color
        else:
            raise ValueError(f"Error: Card {card} is not a PropertyCard.")
        if color not in self.property_sets:
            raise ValueError(f"Error: Player {self.name} does not have any {color} properties.")
        self.property_sets[color].remove_card(card)
        if self.property_sets[color].is_empty:
            del self.property_sets[color]
    
    def remove_property_set(self, property_set_color):
        return self.property_sets.pop(property_set_color)
    
    def add_property_set(self, property_set_color, property_set):
        self.property_sets[property_set_color] = property_set
    
    def has_card(self, card_name: str):
        #dont leak whats in player's hand
        for card in self.bank:
            if card.name == card_name:
                return True
        for prop_set in self.property_sets.values():
            if prop_set.has_card(card_name):
                return True
        return False

    def get_card_from_properties(self, info: 'ActionPropertyInfo'):
        """Retrieve a property card object given its name and color."""
        prop_set = self.property_sets[info.prop_color]
        for card in prop_set.cards:
            if card.name == info.name:
                return card
        return None

    def get_bank_value(self) -> int:
        """Calculates the total monetary value of cards in the bank."""
        # Assumes cards in bank have a 'value' attribute
        return sum(card.value for card in self.bank)

    def get_property_sets(self) -> Dict[PropertyColor, PropertySet]:
        """Returns the dictionary of property sets."""
        return self.property_sets

    def to_json(self, debug=False) -> Dict[str, Any]:
        if debug:
            return {
            "name": self.name,
            "hand_count": len(self.hand),
            "hand_cards": [card.to_json() for card in self.hand],
            "banked_cards": [card.to_json() for card in self.bank],
            "bank_value": self.get_bank_value(),
            "property_sets": {
                color.name: prop_set.to_json()
                for color, prop_set in self.property_sets.items()
            }
        }
        return {
            "name": self.name,
            "hand_count": len(self.hand),
            "banked_cards": [card.to_json() for card in self.bank],
            "bank_value": self.get_bank_value(),
            "property_sets": {
                color.name: prop_set.to_json()
                for color, prop_set in self.property_sets.items()
            }
        }

    @property
    def cards_in_hand(self):
        return len(self.hand)

    @abstractmethod
    def get_action(self, game_state_dict: dict, game_history: List[str]) -> Any: # Placeholder for GameState and Action types
        """
        Determines the action the player wants to take based on the game state.
        This must be implemented by subclasses (e.g., HumanPlayer, AIPlayer).

        Args:
            game_state: The current state of the game as json
            game_history: List of strings representing the set of actions taken so far in the game

        Returns:
            An object representing the chosen action (details TBD).
        """
        pass

    @abstractmethod
    def choose_cards_to_discard(self, num_cards_to_discard, game_state_dict, game_history: List[str]) -> Any:
        pass

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name='{self.name}')" # Use type(self) for subclass representation

    def __eq__(self, other) -> bool:
        if not isinstance(other, Player):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)
    
    @abstractmethod
    def provide_payment(self, reason: str, amount: int, game_state_dict: dict, game_history: List[str]) -> List[Card]:
        pass

    @abstractmethod
    def wants_to_negate(self, action_chain_str: str, target_player_name: str, game_state_dict: dict, game_history: List[str]) -> Optional[Action]:
        pass
        