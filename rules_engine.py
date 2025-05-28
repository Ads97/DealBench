from typing import Any, List, Tuple
from action import Action, ActionType
from card import CardType, PropertyColor, PropertyCard, RentCard, BuildingCard, ActionCard, Card # etc.
from player import Player

"""https://www.buffalolib.org/sites/default/files/gaming-unplugged/inst/Monopoly%20Deal%20Card%20Game%20Instructions.pdf"""

class RulesEngine:
    @staticmethod
    def validate_action(action: Action, current_player: Player) -> bool:
        """Validates if a proposed action is legal according to game rules."""
        print(f"Validating Action: {action}") # Debug print
        if not action.card:
            return False

        if action.source_player != current_player:
            # Allow JustSayNo validation even out of turn?
            if action.card.get_card_type() != CardType.ACTION_RESPONSE:
                 print(f"Validation Error: Not {action.source_player.name}'s turn.")
                 return False

        # Check if player has the card (unless it's a context action like passing)
        if action.card not in action.source_player.hand:
            print(f"Validation Error: {action.source_player.name} does not have {action.card.name}")
            return False
        
        if action.action_type!=ActionType.PLAY_ACTION and action.card.get_card_type() != CardType.ACTION_RENT:
            if action.double_the_rent_count > 0:
                print(f"Validation Error: Double the Rent can only be used with Rent cards. Found {action.card.name} with double the rent count {action.double_the_rent_count}")
                return False

        # --- Card-Specific Validation --- 
        action_type = action.action_type

        if action_type == ActionType.ADD_TO_BANK: # Banking
            return RulesEngine._validate_add_to_bank(action)
        elif action_type == ActionType.ADD_TO_PROPERTIES: # Laying Property
            return RulesEngine._validate_add_to_properties(action)
        elif action_type == ActionType.PLAY_ACTION:
            return RulesEngine._validate_action_card(action)
        elif action_type == ActionType.MOVE_PROPERTY:
            return RulesEngine._validate_move_property(action)
        elif action_type == ActionType.PASS:
            raise ValueError("Pass action should not be validated.")
        
        raise ValueError(f"Invalid action type: {action_type}")

    @staticmethod
    def _validate_add_to_properties(action: Action) -> bool:
        if action.target_property_set is None:
            print(f"Validation Error: Target property set {action.target_property_set} is None.")
            return False
        if len(action.target_player_names) > 0:
            print(f"Validation Error: {action.target_player_names} is not None.")
            return False
        if action.card.get_card_type() not in [CardType.PROPERTY, CardType.PROPERTY_WILD]:
            print(f"Validation Error: {action.card.name} is not a property card.")
            return False
        return True
    
    @staticmethod
    def _validate_add_to_bank(action: Action) -> bool:
        if not action.card.can_use_as_money:
            print(f"Validation Error add to bank cannot use card {action.card.name}.")
            return False
        if len(action.target_player_names) > 0:
            print(f"Validation Error add to bank cannot have target players. {action.target_player_names}")
            return False
        if action.target_property_set is not None:
            print(f"Validation Error add to bank cannot have target property set.")
            return False
        return True
    
    @staticmethod
    def _validate_action_card(action: Action) -> bool:
        if action.card.get_card_type() not in (CardType.ACTION, CardType.ACTION_RENT, CardType.ACTION_BUILDING, CardType.ACTION_DOUBLE_THE_RENT, CardType.ACTION_RESPONSE, CardType.ACTION_OTHER):
            return False
        if action.target_property_set is not None:
            return False
        
        match action.card.get_card_type():
            case CardType.ACTION_RENT:
                return RulesEngine._validate_rent(action)
            case CardType.ACTION_BUILDING:
                return RulesEngine._validate_building(action)
            case CardType.ACTION_DOUBLE_THE_RENT:
                return RulesEngine._validate_double_the_rent(action)
            case CardType.ACTION_RESPONSE:
                return RulesEngine._validate_response(action)
            case CardType.ACTION_OTHER:
                return RulesEngine._validate_other(action)
        return True

    @staticmethod
    def _validate_rent(action: Action) -> bool: #TODO: add validation for whether there's enough turns left to play double the rent. 
        if action.card.is_wild:
            if len(action.target_player_names) != 1:
                print(f"Validation Error (Rent): Wild rent card must have exactly one target player.")
                return False
            
        players_properties = action.source_player.get_property_sets()
        if action.rent_color not in players_properties.keys():
            print(f"Validation Error (Rent): Player {action.source_player.name} does not have any {action.rent_color} properties.")
            return False
        if not action.card.is_wild and (action.rent_color not in action.card.colors):
            print(f"Validation Error (Rent): rent colour {action.rent_color} not valid for card {action.card.name} with colours {action.card.colors}.")
            return False
        return True

    @staticmethod
    def validate_rent_payment(payment_cards: List[Tuple[Card, str]]):
        for card, source in payment_cards:
            if source=="property":
                if card.get_card_type() == CardType.ACTION_BUILDING:
                    print("Validation error: Cannot pay with building card in properties.")
                    return False
            if source=="hand":
                print(f"Validation error: Cannot pay with cards from hand. {card.name}")
                return False
        return True

    def _validate_building(self, action: Action) -> bool:
        card: BuildingCard = action.card
        target_color = action.additional_details.get('target_set_color')
        if not isinstance(target_color, PropertyColor):
            print("Validation Error (Building): Target set color missing or invalid type.")
            return False
        if target_color in [PropertyColor.RAILROAD, PropertyColor.UTILITY]:
            print("Validation Error (Building): Cannot build on Railroads or Utilities.")
            return False

        player_state = self.game_state.players[action.source_player.name]
        properties = player_state.properties
        if target_color not in properties:
            print(f"Validation Error (Building): Player does not have any {target_color} properties.")
            return False

        set_data = properties[target_color]
        # Check for completed set
        if not self.is_set_complete(player_state, target_color):
             print(f"Validation Error (Building): Set {target_color} is not complete.")
             return False

        # Check building-specific rules (House/Hotel placement)
        # This logic was previously in the card itself, now moved here.
        if card.building_type == 'house':
            has_house = set_data.get('houses', 0) > 0
            if has_house:
                print(f"Validation Error (House): Set {target_color} already has a house.")
                return False
        elif card.building_type == 'hotel':
            has_house = set_data.get('houses', 0) > 0
            has_hotel = set_data.get('hotels', 0) > 0
            if not has_house:
                 print(f"Validation Error (Hotel): Set {target_color} needs a house first.")
                 return False
            if has_hotel:
                 print(f"Validation Error (Hotel): Set {target_color} already has a hotel.")
                 return False

        return True
        
        
    
    def is_set_complete(self, player: Player, color: PropertyColor) -> bool:
        """Checks if the player has a complete set of the given color."""
        color_key = color.name
        if color_key not in player['properties']:
            return False

        set_data = player['properties'][color_key]
        cards_in_set = set_data['cards']
        if not cards_in_set:
            return False

        # Find the required number (tricky with only wildcards)
        required_count = 0
        for card in cards_in_set:
            if isinstance(card, PropertyCard) and not isinstance(card, WildPropertyCard):
                required_count = card.properties_in_set
                break
        # If only wildcards, need a way to know required count (maybe store on set_data?)
        if required_count == 0:
             print(f"Warning: Cannot determine required count for set {color_key} (only wildcards?). Needs refinement.")
             # TODO: How to handle sets made purely of wildcards?
             # For now, assume requires looking up from config based on color.
             return False # Cannot determine completion yet

        return len(cards_in_set) >= required_count
    
    @staticmethod
    def check_win_condition(player: Player) -> bool:
        """Checks if any player has met the win condition (3 full sets)."""
        property_sets = player.get_property_sets()
        win_set = set()
        for color, prop_set in property_sets.items():
            if prop_set.is_full_set:
                win_set.add(color)
        return len(win_set) >= 3
