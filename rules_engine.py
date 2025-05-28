from typing import Any, List, Tuple
from action import Action, ActionType
from card import CardType, PropertyColor, PropertyCard, RentCard, BuildingCard, ActionCard, Card # etc.
from player import Player
from deck_config import ACTIONS_PER_TURN

class RulesEngine:
    @staticmethod
    def validate_action(action: Action, current_player: Player, actions_played: int) -> bool:
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
            return RulesEngine._validate_action_card(action, actions_played)
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
    def _validate_action_card(action: Action, actions_played: int) -> bool:
        if action.card.get_card_type() not in (CardType.ACTION, CardType.ACTION_RENT, CardType.ACTION_BUILDING, CardType.ACTION_DOUBLE_THE_RENT, CardType.ACTION_RESPONSE, CardType.ACTION_OTHER):
            return False
        # if action.target_property_set is not None: # Why was this there?
        #     return False
        
        match action.card.get_card_type():
            case CardType.ACTION_RENT:
                return RulesEngine._validate_rent(action, actions_played)
            case CardType.ACTION_BUILDING:
                return RulesEngine._validate_building(action)
            case CardType.ACTION_RESPONSE:
                return RulesEngine._validate_response(action)
            case CardType.ACTION_OTHER:
                return RulesEngine._validate_other(action)
        return True

    @staticmethod
    def _validate_rent(action: Action, actions_played: int) -> bool: #TODO: add validation for whether there's enough turns left to play double the rent. 
        if action.double_the_rent_count > 0:
            actual_double_the_rent_count = sum(
                1 for c in action.source_player.hand if getattr(c, "get_card_type", lambda: None)() == CardType.ACTION_DOUBLE_THE_RENT
            )
            if actual_double_the_rent_count < action.double_the_rent_count:
                print(f"Validation Error: Not enough Double the Rent cards. Found {actual_double_the_rent_count}, needed {action.double_the_rent_count}")
                return False
        
        actions_needed_for_turn = 1 + action.double_the_rent_count
        if actions_played + actions_needed_for_turn > ACTIONS_PER_TURN:
            print(f"Validation Error: Not enough actions left in turn to play this rent. Need {actions_needed_for_turn}, have {ACTIONS_PER_TURN - actions_played}")
            return False

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

    @staticmethod
    def _validate_building(action: Action) -> bool:
        if action.target_property_set is None:
            print(f"Validation Error: No target property set specified for building action.")
            return False
            
        # Check if the player has the property set
        player_property_sets = action.source_player.get_property_sets()
        if action.target_property_set not in player_property_sets:
            print(f"Validation Error: Player {action.source_player.name} does not have a {action.target_property_set} property set.")
            return False
            
        target_set = player_property_sets[action.target_property_set]
        building_type = action.card.building_type
        
        # Check if the set is a full set
        if not target_set.is_full_set:
            print(f"Validation Error: Cannot add {building_type} to incomplete property set {action.target_property_set}.")
            return False
            
        # Check if the set can have buildings (no buildings on railroads or utilities)
        if action.target_property_set in [PropertyColor.RAILROAD, PropertyColor.UTILITY]:
            print(f"Validation Error: Cannot add buildings to {action.target_property_set} properties.")
            return False
            
        # Check building-specific rules
        if building_type == "house":
            if target_set.has_house or target_set.has_hotel:
                print(f"Validation Error: Property set {action.target_property_set} already has a house or hotel.")
                return False
        elif building_type == "hotel":
            if not target_set.has_house:
                print(f"Validation Error: Cannot add a hotel to {action.target_property_set} without a house.")
                return False
            if target_set.has_hotel:
                print(f"Validation Error: Property set {action.target_property_set} already has a hotel.")
                return False
        else:
            print(f"Validation Error: Unknown building type: {building_type}")
            return False
            
        return True
    
    @staticmethod
    def check_win_condition(player: Player) -> bool:
        """Checks if any player has met the win condition (3 full sets)."""
        property_sets = player.get_property_sets()
        win_set = set()
        for color, prop_set in property_sets.items():
            if prop_set.is_full_set:
                win_set.add(color)
        return len(win_set) >= 3
