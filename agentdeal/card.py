from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import List, Tuple, Optional, Dict, Any

# --- Enums for Clarity ---

class CardType(Enum):
    MONEY = auto()
    PROPERTY = auto()
    ACTION = auto()
    PROPERTY_WILD = auto()
    ACTION_RENT = auto()
    ACTION_BUILDING = auto()
    ACTION_DOUBLE_THE_RENT = auto() # e.g., Double the Rent
    ACTION_JUST_SAY_NO = auto() # e.g., Just Say No
    ACTION_PASS_GO = auto()
    ACTION_BIRTHDAY = auto()
    ACTION_DEBT_COLLECTOR = auto()
    ACTION_DEAL_BREAKER = auto()
    ACTION_SLY_DEAL = auto()
    ACTION_FORCED_DEAL = auto()

class PropertyColor(Enum):
    BROWN = auto()
    LIGHT_BLUE = auto()
    PINK = auto()
    ORANGE = auto()
    RED = auto()
    YELLOW = auto()
    GREEN = auto()
    DARK_BLUE = auto()
    RAILROAD = auto()
    UTILITY = auto()
    # Wildcard colors can be represented by None or a special value if needed separate from card type
    ALL = auto() # For 4-color wild card or multi-color rent

# --- Base Card Class ---

class Card(ABC):
    """Abstract Base Class for all cards in Monopoly Deal."""
    def __init__(self, name: str, value: int):
        """
        Args:
            name: The display name of the card (e.g., \"$5M\", \"Boardwalk\", \"Rent (Blue/Green)\").
            value: The monetary value when used for payment or banked (can be 0).
        """
        self.name = name
        self.value = value

    @abstractmethod
    def get_card_type(self) -> CardType:
        """Returns the specific type of the card using the CardType enum."""
        pass

    @property
    def can_use_as_money(self) -> bool:
        return True


    def __repr__(self) -> str:
        return f"{type(self).__name__}(name=\'{self.name}\', value={self.value})"

    def __hash__(self) -> int:
        # Basic hash based on name and type
        return hash((self.name, self.get_card_type()))

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.get_card_type().name
        }

# --- Concrete Card Types ---

class MoneyCard(Card):
    """Represents a money card used purely for banking and payment."""
    def get_card_type(self) -> CardType:
        return CardType.MONEY

class PropertyCard(Card):
    """Represents a standard property card belonging to a specific color set."""
    def __init__(self, name: str, value: int, set_color: PropertyColor, rent_values: List[int], properties_in_set: int):
        super().__init__(name, value)
        if not isinstance(set_color, PropertyColor) or set_color == PropertyColor.ALL:
            raise ValueError("Standard PropertyCard must have a specific color.")
        if not rent_values or not isinstance(rent_values, list):
            raise ValueError("PropertyCard must have a list of rent values.")
        if properties_in_set <= 0:
            raise ValueError("PropertyCard must require at least 1 property in its set.")

        self.set_color = set_color
        self.rent_values = rent_values # List: rent for 1 prop, 2 props, ..., full set
        self.properties_in_set = properties_in_set # How many needed for a full set

    def get_card_type(self) -> CardType:
        return CardType.PROPERTY

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name=\'{self.name}\', value={self.value}, color={self.set_color.name})"

    def to_json(self) -> Dict[str, Any]:
        data = super().to_json()
        data.update({
            "set_color": self.set_color.name,
            "rent_values": self.rent_values,
            "num_properties_for_full_set": self.properties_in_set
        })
        return data
    
    def get_color(self) -> PropertyColor:
        return self.set_color

class WildPropertyCard(PropertyCard):
    """Represents a property wild card that can represent multiple colors."""
    def __init__(self, name: str, value: int, available_colors: List[PropertyColor], rent_values: Optional[Dict[PropertyColor, List[int]]] = None, properties_in_set: Optional[Dict[PropertyColor, int]] = None):
        Card.__init__(self, name, value) # Initialize Card attributes: name, value
        
        self.available_colors = available_colors
        self.current_color: Optional[PropertyColor] = None

        if not available_colors:
            raise ValueError("WildPropertyCard must have available colors.")
        # Reset attributes not applicable in the same way as standard properties
        self.rent_values = rent_values
        self.properties_in_set = properties_in_set

    def get_card_type(self) -> CardType:
        return CardType.PROPERTY_WILD

    def set_wild_color(self, color: PropertyColor):
        """Sets the color this wild card represents (must be one of its available colors)."""
        if color in self.available_colors:
            self.current_color = color
        else:
            raise ValueError(f"Invalid color {color} for this wild card. Available: {self.available_colors}")

    def clear_wild_color(self):
        """Resets the color choice."""
        self.current_color = None
    
    def get_color(self) -> PropertyColor:
        if self.current_color is None:
            raise ValueError("WildPropertyCard has no color set.")
        return self.current_color
    
    @property
    def can_use_as_money(self) -> bool:
        return False

    def __repr__(self) -> str:
        current_color_str = f", current={self.current_color.name}" if self.current_color else ""
        colors_str = "/\\".join(c.name for c in self.available_colors)
        return f"{type(self).__name__}(name='{self.name}', value={self.value}, colors=[{colors_str}]{current_color_str})"

    def to_json(self) -> Dict[str, Any]:
        # Call Card's base to_json() equivalent, as PropertyCard's to_json() adds fields not directly applicable here.
        # Assumes self.name and self.value are set correctly by WildPropertyCard's __init__ (e.g. by calling Card.__init__)
        data = {
            "name": self.name, 
            "value": self.value, 
            "type": self.get_card_type().name
        }
        data.update({
            "available_colors": [color.name for color in self.available_colors],
            "current_color": self.current_color.name if self.current_color else None
        })
        return data


class ActionCard(Card):
    """Base class for cards that trigger an action when played."""
    # Most action cards are discarded after play, but some (House/Hotel) persist.
    # Subclasses will define specific behavior attributes.
    def get_card_type(self) -> CardType:
        # Default, subclasses should override if more specific type exists
        return CardType.ACTION_OTHER

    def to_json(self) -> Dict[str, Any]:
        return super().to_json()

# --- Specific Action Card Types ---

class RentCard(ActionCard):
    """Action card to collect rent from other players."""
    def __init__(self, name: str, value: int, colors: List[PropertyColor], wild: bool):
        super().__init__(name, value)
        if not colors:
             raise ValueError("RentCard must target at least one color.")
        self.colors = colors # List of colors rent can be charged for
        self.wild = wild

    def get_card_type(self) -> CardType:
        return CardType.ACTION_RENT

    def __repr__(self) -> str:
        colors_str = ",".join(c.name for c in self.colors) 
        return f"{type(self).__name__}(name='{self.name}', value={self.value}, colors=[{colors_str}])"

    def to_json(self) -> Dict[str, Any]:
        data = super().to_json()
        data.update({
            "colors": [color.name for color in self.colors]
        })
        return data
    
    @property
    def is_wild(self) -> bool:
        return self.wild

class BuildingCard(ActionCard):
    """Abstract base for House and Hotel cards."""
    def __init__(self, name: str, value: int, building_type: str):
        super().__init__(name, value)
        self.building_type = building_type # "house" or "hotel"

    def get_card_type(self) -> CardType:
        return CardType.ACTION_BUILDING

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name='{self.name}', value={self.value}, type='{self.building_type}')"

    def to_json(self) -> Dict[str, Any]:
        data = super().to_json()
        data.update({
            "building_type": self.building_type
        })
        return data

class HouseCard(BuildingCard):
    """Adds a House to a completed property set (excluding Railroad/Utility)."""
    def __init__(self, name: str, value: int):
        super().__init__(name, value, building_type="house")

class HotelCard(BuildingCard):
    """Adds a Hotel to a completed property set that already has a House."""
    def __init__(self, name: str, value: int):
        super().__init__(name, value, building_type="hotel")

class DoubleTheRentCard(ActionCard):
    """Action card that doubles the next rent card played."""
    def get_card_type(self) -> CardType:
        return CardType.ACTION_DOUBLE_THE_RENT

class JustSayNoCard(ActionCard):
    """Action card to cancel an action targeting the player."""
    def get_card_type(self) -> CardType:
        return CardType.ACTION_JUST_SAY_NO

class PassGoCard(ActionCard):
    """Action card that allows the player to collect 2 extra cards from the deck."""
    def get_card_type(self) -> CardType:
        return CardType.ACTION_PASS_GO

class ItsMyBirthdayCard(ActionCard):
    """Action card that allows the player to collect $2M from the bank."""
    def get_card_type(self) -> CardType:
        return CardType.ACTION_BIRTHDAY

class DebtCollectorCard(ActionCard):
    """Action card that allows the player to collect $2M from the bank."""
    def get_card_type(self) -> CardType:
        return CardType.ACTION_DEBT_COLLECTOR

class DealBreakerCard(ActionCard):
    """Action card that allows the player to collect $2M from the bank."""
    def get_card_type(self) -> CardType:
        return CardType.ACTION_DEAL_BREAKER

class SlyDealCard(ActionCard):
    """Action card that allows the player to collect $2M from the bank."""
    def get_card_type(self) -> CardType:
        return CardType.ACTION_SLY_DEAL

class ForcedDealCard(ActionCard):
    """Action card that allows the player to collect $2M from the bank."""
    def get_card_type(self) -> CardType:
        return CardType.ACTION_FORCED_DEAL

class PropertySet():
    def __init__(self, card: Card):
        if not isinstance(card, PropertyCard) and not isinstance(card, WildPropertyCard):
            raise ValueError("PropertySet must be initialized with a PropertyCard or WildPropertyCard.")
        if isinstance(card, WildPropertyCard):
            self.set_color = card.current_color
        else:
            self.set_color = card.set_color
        self.cards: List[Card] = [] # Will store PropertyCard or WildPropertyCard
        self.number_for_full_set: int = 0 # Will be set by the first property card added
        self.has_house: bool = False
        self.has_hotel: bool = False
        self.add_card(card)

    def add_card(self, card: Card):
        """Adds a property card to the set."""
        if isinstance(card, WildPropertyCard):
            # Assuming wild card's current_color is set appropriately before adding
            if card.current_color == self.set_color:
                self.cards.append(card)
        elif isinstance(card, PropertyCard) and card.set_color == self.set_color:
            if self.number_for_full_set == 0:
                self.number_for_full_set = card.properties_in_set
            self.cards.append(card)
        elif isinstance(card, BuildingCard):
            if card.building_type == "house":
                self.has_house = True
            elif card.building_type == "hotel" and self.has_house:
                self.has_hotel = True
            else:
                raise ValueError(f"Could not add building card {card} to property set {self.set_color}. Perhaps you're trying to add a hotel before a house?")
        else:
            raise ValueError(f"Card {card} is not a PropertyCard or BuildingCard.")

    def remove_card(self, card_to_remove: Card):
        """Removes a specific card from the set."""
        if card_to_remove in self.cards:
            self.cards.remove(card_to_remove)
            if not self.cards:
                self.number_for_full_set = 0 # Reset if set becomes empty
                self.has_house = False # Cannot have buildings on an empty set
                self.has_hotel = False
        else:
            raise ValueError(f"Card {card_to_remove} not found in set {self.cards}")
    
    def has_card(self, card_name: str):
        for card in self.cards:
            if card.name == card_name:
                return True
        return False
    
    def get_card(self, card_name: str):
        for card in self.cards:
            if card.name == card_name:
                return card
        raise ValueError(f"Card {card_name} not found in set {self.set_color}. Full set description {self}")

    @property
    def is_full_set(self) -> bool:
        """Checks if the property set is complete."""
        if self.number_for_full_set: # Cannot be full if requirement is unknown
            return len(self.cards) >= self.number_for_full_set
        else:
            return False
    
    @property
    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def get_rent_value(self) -> int:
        if not self.cards:
            raise ValueError("Tried to get rent for empty property set. Empty property sets should not be possible.")
        
        # Get the rent values from the first non-wild card in the set
        rent_values = 0
        for card in self.cards:
            if card.value!=0: #any color wild cards dont have rent values
                if isinstance(card, WildPropertyCard):
                    rent_values = card.rent_values[self.set_color]
                else:
                    rent_values = card.rent_values
                break
        
        if rent_values == 0:
            return 0
        
        num_properties = len(self.cards)
        rent_index = min(num_properties - 1, len(rent_values) - 1)
        base_rent = rent_values[rent_index]
        
        # Apply modifiers for house and hotel
        if self.has_house:
            base_rent += 3
        if self.has_house and self.has_hotel:
            base_rent += 4
        
        return base_rent

    def total_value(self) -> int:
        return sum(card.value for card in self.cards)


    def can_add_building(self, building_type: str) -> bool:
        """Checks if a house or hotel can be added."""
        if not self.is_full_set():
            return False
        if self.set_color in [PropertyColor.RAILROAD, PropertyColor.UTILITY]:
            return False
        
        if building_type == "house":
            return not self.has_house and not self.has_hotel
        elif building_type == "hotel":
            return self.has_house and not self.has_hotel
        return False

    def add_building(self, building_card: BuildingCard) -> bool:
        if not self.can_add_building(building_card.building_type):
            return False
        
        if building_card.building_type == "house":
            self.has_house = True
            return True
        elif building_card.building_type == "hotel":
            self.has_hotel = True
            return True
        return False

    def __repr__(self) -> str:
        card_names = sorted([c.name for c in self.cards]) # Sort for consistent output
        status = "Full Set" if self.is_full_set() else f"{len(self.cards)}/{self.number_for_full_set or '?'}"
        buildings = ""
        if self.has_hotel:
            buildings = " (Hotel)"
        elif self.has_house:
            buildings = " (House)"
        # Pass a dummy game_rules if needed for __repr__ rent calculation, or make get_rent simpler for repr
        rent_display = self.get_rent() # This might need game_rules for full accuracy in some edge cases
        return f"PropertySet({self.set_color.name}, {status}{buildings}, Cards: {card_names}, Rent: ${rent_display})"

    def to_json(self) -> Dict[str, Any]:
        return {
            "set_color": self.set_color.name if self.set_color else "Wild cards",
            "cards": [card.to_json() for card in self.cards],
            "number_for_full_set": self.number_for_full_set,
            "is_full_set": self.is_full_set,
            "has_house": self.has_house,
            "has_hotel": self.has_hotel,
            "rent": self.get_rent_value()
        }



# --- TODO: Add other action cards as needed ---
# class DealBreakerCard(ActionCard): ...
# class SlyDealCard(ActionCard): ...
# class ForcedDealCard(ActionCard): ...
# class DebtCollectorCard(ActionCard): ...
# class ItsMyBirthdayCard(ActionCard): ...
