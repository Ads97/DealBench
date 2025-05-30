from typing import List, Optional
from card import BuildingCard, Card, PropertyCard, WildPropertyCard, PropertyColor
from player import Player 
from dataclasses import dataclass
from enum import Enum, auto

class ActionType(Enum):
    ADD_TO_PROPERTIES = auto()         # Placing property on table
    ADD_TO_BANK = auto()            # Adding money to bank
    PAY_PLAYER = auto()            # Paying another player
    
    PLAY_ACTION = auto()           # Playing an action card
    MOVE_PROPERTY = auto()         # Moving a property card to a different set. Does not count as an action
    PASS = auto()                  # Passing turn


@dataclass
class Action:

    def __init__(self,
        action_type: ActionType,
        source_player: Player, 
        card: Optional[Card] = None, # Card object being played
        target_player_names: Optional[List[str]] = None, # List of Player names, if applicable
        target_property_set: Optional[PropertyColor] = None,
        rent_color: Optional[PropertyColor] = None,
        double_the_rent_count: Optional[int] = 0,
        sly_deal_property: Optional[PropertyCard] = None):
        """Represents a game action taken by a player."""
        self.action_type = action_type
        self.source_player = source_player
        self.card = card
        self.target_player_names = target_player_names if target_player_names is not None else []
        self.target_property_set = None
        self.double_the_rent_count = double_the_rent_count
        if action_type == ActionType.ADD_TO_PROPERTIES:
            if isinstance(card, WildPropertyCard):
                self.target_property_set = target_property_set
            elif isinstance(card, PropertyCard):
                self.target_property_set = card.set_color
        else:
            self.target_property_set = target_property_set
        self.rent_color = rent_color
        self.sly_deal_property = sly_deal_property

    def __repr__(self) -> str:
        """Return a detailed string representation of the Action."""
        components = [
            f"Action(type={self.action_type.name}",
            f"player='{getattr(self.source_player, 'name', 'Unknown')}'"
        ]
    
        if self.card:
            components.append(f"card='{getattr(self.card, 'name', 'Unknown')}'")
    
        if self.target_player_names:
            components.append(f"targets={self.target_player_names}")
    
        if self.target_property_set:
            components.append(f"property_set={self.target_property_set.name}")
    
        if self.rent_color:
            components.append(f"rent_color={self.rent_color.name}")
        
        if self.double_the_rent_count:
            components.append(f"double_the_rent_count={self.double_the_rent_count}")
        
        if self.sly_deal_property:
            components.append(f"sly_deal_property={self.sly_deal_property.name}")
    
        return f"<{', '.join(components)}>"