import random
from typing import List, Optional, Dict, Any

# Import necessary classes and enums
from card import (
    Card, CardType, PropertyColor,
    MoneyCard, PropertyCard, WildPropertyCard, RentCard, BuildingCard, HouseCard, HotelCard,
    DoubleTheRentCard, JustSayNoCard, ActionCard, PassGoCard # Assuming other specific action cards might be needed later
)
from deck_config import DECK_CONFIGURATION # Import the configuration

class Deck:
    """Manages the deck of undrawn cards for the game."""

    def __init__(self):
        """Initializes the deck by creating and shuffling all cards from the config."""
        self._cards: List[Card] = []
        self._discard_pile: List[Card] = []
        self._create_new_deck()

    def _create_new_deck(self):
        """Populates and shuffles the deck based on DECK_CONFIGURATION."""
        self._cards = [] # Reset the deck
        print("Creating new deck from configuration...")
        card_creation_errors = []

        for item in DECK_CONFIGURATION:
            cards_to_add = self._instantiate_cards(item)
            if cards_to_add:
                self._cards.extend(cards_to_add)
            else:
                card_creation_errors.append(f"Could not instantiate card: {item.get('name')}")


        if card_creation_errors:
            print("\n--- Errors during deck creation ---")
            for error in card_creation_errors:
                print(error)
            print("-------------------------------------")
            # Decide if you want to raise an error or continue with a partial deck
            # raise RuntimeError("Errors occurred during deck creation.")

        print(f"Deck created with {len(self._cards)} cards.")
        self.shuffle()

    @staticmethod
    def get_rent_and_set_number(color: PropertyColor) -> List[int]:
        rent_info = {
        PropertyColor.BROWN: {'rent_values': [1, 2], 'properties_in_set': 2},
        PropertyColor.LIGHT_BLUE: {'rent_values': [1, 2, 3], 'properties_in_set': 3},
        PropertyColor.PINK: {'rent_values': [1, 2, 4], 'properties_in_set': 3},
        PropertyColor.ORANGE: {'rent_values': [1, 3, 5], 'properties_in_set': 3},
        PropertyColor.RED: {'rent_values': [2, 3, 6], 'properties_in_set': 3},
        PropertyColor.YELLOW: {'rent_values': [2, 4, 6], 'properties_in_set': 3},
        PropertyColor.GREEN: {'rent_values': [2, 4, 7], 'properties_in_set': 3},
        PropertyColor.DARK_BLUE: {'rent_values': [3, 8], 'properties_in_set': 2},
        PropertyColor.RAILROAD: {'rent_values': [1, 2, 3, 4], 'properties_in_set': 4},
        PropertyColor.UTILITY: {'rent_values': [1, 2], 'properties_in_set': 2}
    }
        return rent_info[color]
    
    def _instantiate_cards(self, item: Dict[str, Any]) -> List[Card]:
        """Instantiates the correct Card object(s) based on a config dictionary."""
        card_type = item['type']
        count = item['count']
        name = item['name']
        value = item['value']
        instances = []

        specific_class = None
        args = [name, value]
        kwargs = {}

        if card_type == CardType.MONEY:
            specific_class = MoneyCard
        elif card_type == CardType.PROPERTY:
            specific_class = PropertyCard
            kwargs = {
                'set_color': item['set_color'],
                'rent_values': self.get_rent_and_set_number(item['set_color'])['rent_values'],
                'properties_in_set': self.get_rent_and_set_number(item['set_color'])['properties_in_set']
            }
        elif card_type == CardType.PROPERTY_WILD:
            specific_class = WildPropertyCard
            kwargs = {'available_colors': item['available_colors']}
            if len(item['available_colors']) == 2:
                kwargs['rent_values'] = {
                    item['available_colors'][0]: self.get_rent_and_set_number(item['available_colors'][0])['rent_values'],
                    item['available_colors'][1]: self.get_rent_and_set_number(item['available_colors'][1])['rent_values']
                }
                kwargs['properties_in_set'] = {
                    item['available_colors'][0]: self.get_rent_and_set_number(item['available_colors'][0])['properties_in_set'],
                    item['available_colors'][1]: self.get_rent_and_set_number(item['available_colors'][1])['properties_in_set']
                }
        elif card_type == CardType.ACTION_RENT:
            specific_class = RentCard
            kwargs = {'colors': item['colors'], 'wild': item['wild']}
        elif card_type == CardType.ACTION_BUILDING:
            # Use 'card_class' key from config to find the specific building class
            class_name = item.get('card_class')
            if class_name == 'HouseCard':
                specific_class = HouseCard
            elif class_name == 'HotelCard':
                specific_class = HotelCard
            else:
                raise ValueError(f"Unknown building card class: {class_name}")
        elif card_type == CardType.ACTION_DOUBLE_THE_RENT:
            class_name = item.get('card_class')
            if class_name == 'DoubleTheRentCard':
                 specific_class = DoubleTheRentCard
            else:
                 raise ValueError(f"Unknown modifier card class: {class_name}")
        elif card_type == CardType.ACTION_JUST_SAY_NO:
            class_name = item.get('card_class')
            if class_name == 'JustSayNoCard':
                 specific_class = JustSayNoCard
            else:
                 raise ValueError(f"Unknown response card class: {class_name}")
        elif card_type == CardType.ACTION_PASS_GO:
            class_name = item.get('card_class')
            if class_name == 'PassGoCard':
                 specific_class = PassGoCard
            else:
                 raise ValueError(f"Unknown pass go card class: {class_name}")
        elif card_type == CardType.ACTION_OTHER:
            # For generic actions defined only by name/value in config for now
            # We need a generic ActionCard instance, but ActionCard is ABC.
            # Option 1: Create a concrete GenericActionCard(ActionCard)
            # Option 2: Use a placeholder or skip instantiation if ActionHandler only needs type/name
            # Let's skip instantiation for ACTION_OTHER for now, assuming handler uses config info.
            # OR, we could instantiate a base ActionCard if it were not abstract.
            # For simplicity now, let's assume a generic ActionCard can be made (modify card.py if needed)
            # print(f"Warning: ACTION_OTHER ({name}) configured but no specific class. Creating generic ActionCard.")
            # specific_class = ActionCard # This would fail if ActionCard is ABC and has abstract methods
            # If ActionCard becomes concrete or we add GenericActionCard:
            # kwargs = {'action_name': item.get('action_name')}
            print(f"Skipping instantiation for ACTION_OTHER: {name} (needs concrete class or handler logic)")
            return [] # Don't create instances for now

        else:
            raise ValueError(f"Unhandled card type in configuration: {card_type}")

        if specific_class:
            for _ in range(count):
                instances.append(specific_class(*args, **kwargs))

        return instances

    def shuffle(self):
        """Shuffles the cards currently in the deck."""
        random.shuffle(self._cards)
        print("Deck shuffled.")

    def draw_card(self) -> Optional[Card]:
        """Removes and returns the top card from the deck. Returns None if empty."""
        if not self._cards:
            raise ValueError("No cards left in the deck.")
        return self._cards.pop()
    
    def discard_card(self, card: Card):
        """Adds a card to the discard pile."""
        self._discard_pile.append(card)

    @property
    def cards_left(self) -> int:
        """Returns the number of cards remaining in the deck."""
        return len(self._cards)
    
    @property
    def total_cards(self) -> int:
        return len(self._cards) + len(self._discard_pile)
