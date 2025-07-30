import random
from typing import List, Optional, Dict, Any

# Import necessary classes and enums
from dealbench.card import (
    Card, CardType, PropertyColor,
    MoneyCard, PropertyCard, WildPropertyCard, RentCard, BuildingCard, HouseCard, HotelCard,
    DoubleTheRentCard, JustSayNoCard, ActionCard, PassGoCard, ItsMyBirthdayCard, DebtCollectorCard,
    SlyDealCard, ForcedDealCard, DealBreakerCard
)
from dealbench.deck_config import DECK_CONFIGURATION, RENT_INFO  # Import the configuration
import logging
logger = logging.getLogger(__name__)

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
        logger.info("Creating new deck from configuration...")
        card_creation_errors = []

        for item in DECK_CONFIGURATION:
            cards_to_add = self._instantiate_cards(item)
            if cards_to_add:
                self._cards.extend(cards_to_add)
            else:
                card_creation_errors.append(f"Could not instantiate card: {item.get('name')}")


        if card_creation_errors:
            logger.error("\n--- Errors during deck creation ---")
            for error in card_creation_errors:
                logger.error(error)
            # Decide if you want to raise an error or continue with a partial deck
            # raise RuntimeError("Errors occurred during deck creation.")

        logger.info(f"Deck created with {len(self._cards)} cards.")
        self.shuffle()

    @staticmethod
    def get_rent_and_set_number(color: PropertyColor) -> List[int]:
        return RENT_INFO[color]
    
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
        elif card_type == CardType.ACTION_BIRTHDAY:
            class_name = item.get('card_class')
            if class_name == 'ItsMyBirthdayCard':
                 specific_class = ItsMyBirthdayCard
            else:
                 raise ValueError(f"Unknown birthday card class: {class_name}")
        elif card_type == CardType.ACTION_DEBT_COLLECTOR:
            class_name = item.get('card_class')
            if class_name == 'DebtCollectorCard':
                 specific_class = DebtCollectorCard
            else:
                 raise ValueError(f"Unknown debt collector card class: {class_name}")
        elif card_type == CardType.ACTION_SLY_DEAL:
            class_name = item.get('card_class')
            if class_name == 'SlyDealCard':
                 specific_class = SlyDealCard
            else:
                 raise ValueError(f"Unknown sly deal card class: {class_name}")
        elif card_type == CardType.ACTION_FORCED_DEAL:
            class_name = item.get('card_class')
            if class_name == 'ForcedDealCard':
                 specific_class = ForcedDealCard
            else:
                 raise ValueError(f"Unknown forced deal card class: {class_name}")
        elif card_type == CardType.ACTION_DEAL_BREAKER:
            class_name = item.get('card_class')
            if class_name == 'DealBreakerCard':
                 specific_class = DealBreakerCard
            else:
                 raise ValueError(f"Unknown deal breaker card class: {class_name}")
        else:
            raise ValueError(f"Unhandled card type in configuration: {card_type}")

        if specific_class:
            for _ in range(count):
                instances.append(specific_class(*args, **kwargs))

        return instances

    def shuffle(self):
        """Shuffles the cards currently in the deck."""
        random.shuffle(self._cards)
        logger.info("Deck shuffled.")

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
