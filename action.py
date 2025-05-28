from typing import List, Optional, Any
from card import Card, PropertyCard, WildPropertyCard
from player import Player 

from enum import Enum, auto

class ActionType(Enum):
    ADD_TO_PROPERTIES = auto()         # Placing property on table
    ADD_TO_BANK = auto()            # Adding money to bank
    PAY_PLAYER = auto()            # Paying another player
    
    PLAY_ACTION = auto()           # Playing an action card
    MOVE_PROPERTY = auto()         # Moving a property card to a different set. Does not count as an action
    PASS = auto()                  # Passing turn

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from card import Card, PropertyColor, CardType # Added CardType
from player import Player

@dataclass
class Action:

    def __init__(self,
        action_type: ActionType,
        source_player: Player, 
        card: Optional[Card] = None, # Card object being played
        target_player_names: Optional[List[str]] = None, # List of Player names, if applicable
        target_property_set: Optional[PropertyColor] = None,
        rent_color: Optional[PropertyColor] = None,
        double_the_rent_count: Optional[int] = 0):
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
        self.rent_color = rent_color


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
    
        return f"<{', '.join(components)}>"