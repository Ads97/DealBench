from typing import Any, List, Optional, Tuple
from dealbench.action import Action, ActionType, ActionPropertyInfo
from dealbench.card import CardType, PropertyColor, PropertyCard, RentCard, BuildingCard, ActionCard, Card, WildPropertyCard  # etc.
from dealbench.player import Player
from dealbench.deck_config import ACTIONS_PER_TURN

class RulesEngine:
    @staticmethod
    def validate_action(action: Action, current_player: Player, target_players: List[Player], actions_played: Optional[int]) -> Tuple[bool, Optional[str]]:
        """Validates if a proposed action is legal according to game rules."""
        
        if not action:
            return True, None
        
        if action.action_type == ActionType.PASS:
            return True, None
        
        if not action.card:
            return False, "No card provided"

        if action.source_player != current_player:
            return False, "Source player mismatch"

        # Check if player has the card (unless it's a context action like passing)
        if action.card not in action.source_player.hand:
            if not action.action_type == ActionType.MOVE_PROPERTY:
                return False, f"Validation Error: {action.source_player.name} does not have {action.card.name} in hand"
            else:
                found=False
                for prop_set in current_player.get_property_sets().values():
                    if action.card in prop_set.cards:
                        found=True
                        break
                if not found:
                    return False, f"Validation Error: {current_player.name} does not have {action.card.name} in properties"

        if not (action.action_type == ActionType.PLAY_ACTION and action.card.get_card_type() == CardType.ACTION_RENT):
            if action.double_the_rent_count > 0:
                return False, f"Validation Error: Double the Rent can only be used with Rent cards. Found {action.card.name} with double the rent count {action.double_the_rent_count}"

        # --- Card-Specific Validation --- 
        action_type = action.action_type

        if action_type == ActionType.ADD_TO_BANK: # Banking
            return RulesEngine._validate_add_to_bank(action)
        elif action_type == ActionType.ADD_TO_PROPERTIES: # Laying Property
            return RulesEngine._validate_add_to_properties(action)
        elif action_type == ActionType.PLAY_ACTION:
            return RulesEngine._validate_action_card(action, current_player, target_players, actions_played)
        elif action_type == ActionType.MOVE_PROPERTY:
            return RulesEngine._validate_move_property(action)
        elif action_type == ActionType.PASS:
            raise ValueError("Pass action should not be validated.")
        
        raise ValueError(f"Invalid action type: {action_type}")

    @staticmethod
    def _validate_add_to_properties(action: Action) -> Tuple[bool, Optional[str]]:
        if action.target_property_set is None:
            return False, f"Validation Error: Target property set {action.target_property_set} is None."
        if len(action.target_player_names) > 0:
            return False, f"Validation Error: {action.target_player_names} is not None."
        if action.card.get_card_type() not in [CardType.PROPERTY, CardType.PROPERTY_WILD]:
            return False, f"Validation Error: {action.card.name} is not a property card."
        if action.card.get_card_type() == CardType.PROPERTY_WILD:
            if action.target_property_set not in action.card.available_colors:
                return False, f"Validation Error: {action.card} cannot represent {action.target_property_set}."
        else:
            if action.target_property_set != action.card.set_color:
                return False, f"Validation Error: {action.card} cannot represent {action.target_property_set}."
        return True, None
    
    @staticmethod
    def _validate_add_to_bank(action: Action) -> Tuple[bool, Optional[str]]:
        if not action.card.can_use_as_money:
            return False, f"Validation Error add to bank cannot use card {action.card.name}."
        if len(action.target_player_names) > 0:
            return False, f"Validation Error add to bank cannot have target players. {action.target_player_names}"
        if action.target_property_set is not None:
            return False, "Validation Error add to bank cannot have target property set."
        return True, None
    
    @staticmethod
    def _validate_action_card(action: Action, player: Player, target_players: List[Player], actions_played: int) -> Tuple[bool, Optional[str]]:
        if action.card.get_card_type() not in (CardType.ACTION, CardType.ACTION_RENT, CardType.ACTION_BUILDING, CardType.ACTION_DOUBLE_THE_RENT, CardType.ACTION_JUST_SAY_NO, CardType.ACTION_PASS_GO, CardType.ACTION_BIRTHDAY, CardType.ACTION_DEAL_BREAKER, CardType.ACTION_SLY_DEAL, CardType.ACTION_FORCED_DEAL, CardType.ACTION_DEBT_COLLECTOR):
            return False, "Invalid card type"
        
        if action.source_player.name in action.target_player_names:
            return False, "Validation Error: Action cards cannot target the player who played them."
        
        match action.card.get_card_type():
            case CardType.ACTION_RENT:
                return RulesEngine._validate_rent(action, actions_played)
            case CardType.ACTION_BUILDING:
                return RulesEngine._validate_building(action)
            case CardType.ACTION_PASS_GO:
                return RulesEngine._validate_pass_go(action)
            case CardType.ACTION_BIRTHDAY:
                return RulesEngine._validate_birthday(action)
            case CardType.ACTION_DEAL_BREAKER:
                return RulesEngine._validate_deal_breaker(action, player, target_players)
            case CardType.ACTION_SLY_DEAL:
                return RulesEngine._validate_sly_deal(action, player, target_players)
            case CardType.ACTION_FORCED_DEAL:
                return RulesEngine._validate_forced_deal(action, player, target_players)
            case CardType.ACTION_JUST_SAY_NO:
                return RulesEngine._validate_just_say_no(action)
            case CardType.ACTION_DEBT_COLLECTOR:
                return RulesEngine._validate_debt_collector(action)
        return True, None

    @staticmethod
    def _validate_rent(action: Action, actions_played: int) -> Tuple[bool, Optional[str]]: #TODO: add validation for whether there's enough turns left to play double the rent. 
        if action.double_the_rent_count > 0:
            actual_double_the_rent_count = sum(
                1 for c in action.source_player.hand if getattr(c, "get_card_type", lambda: None)() == CardType.ACTION_DOUBLE_THE_RENT
            )
            if actual_double_the_rent_count < action.double_the_rent_count:
                return False, f"Validation Error: Not enough Double the Rent cards. Found {actual_double_the_rent_count}, needed {action.double_the_rent_count}"
        
        actions_needed_for_turn = 1 + action.double_the_rent_count
        if actions_played + actions_needed_for_turn > ACTIONS_PER_TURN:
            return False, f"Validation Error: Not enough actions left in turn to play this rent. Need {actions_needed_for_turn}, have {ACTIONS_PER_TURN - actions_played}"

        if action.card.is_wild:
            if len(action.target_player_names) != 1:
                return False, "Validation Error (Rent): Wild rent card must have exactly one target player."
            
        players_properties = action.source_player.get_property_sets()
        if action.rent_color not in players_properties.keys():
            return False, f"Validation Error (Rent): Player {action.source_player.name} does not have any {action.rent_color} properties."
        if not action.card.is_wild and (action.rent_color not in action.card.colors):
            return False, f"Validation Error (Rent): rent colour {action.rent_color} not valid for card {action.card.name} with colours {action.card.colors}."
        return True, None

    @staticmethod
    def validate_rent_payment(payment_cards: List[Tuple[Card, str]])-> Tuple[bool, Optional[str]]:
        for card, source in payment_cards:
            if source == "property":
                if card.get_card_type() == CardType.ACTION_BUILDING:
                    return False, "Validation error: Cannot pay with building card in properties."
            if source == "hand":
                return False, f"Validation error: Cannot pay with cards from hand. {card.name}"
        return True, None

    @staticmethod
    def _validate_building(action: Action) -> Tuple[bool, Optional[str]]:
        if action.target_property_set is None:
            return False, "Validation Error: No target property set specified for building action."
            
        # Check if the player has the property set
        player_property_sets = action.source_player.get_property_sets()
        if action.target_property_set not in player_property_sets:
            return False, f"Validation Error: Player {action.source_player.name} does not have a {action.target_property_set} property set."
            
        target_set = player_property_sets[action.target_property_set]
        building_type = action.card.building_type
        
        # Check if the set is a full set
        if not target_set.is_full_set:
            return False, f"Validation Error: Cannot add {building_type} to incomplete property set {action.target_property_set}."
            
        # Check if the set can have buildings (no buildings on railroads or utilities)
        if action.target_property_set in [PropertyColor.RAILROAD, PropertyColor.UTILITY]:
            return False, f"Validation Error: Cannot add buildings to {action.target_property_set} properties."
            
        # Check building-specific rules
        if building_type == "house":
            if target_set.has_house or target_set.has_hotel:
                return False, f"Validation Error: Property set {action.target_property_set} already has a house or hotel."
        elif building_type == "hotel":
            if not target_set.has_house:
                return False, f"Validation Error: Cannot add a hotel to {action.target_property_set} without a house."
            if target_set.has_hotel:
                return False, f"Validation Error: Property set {action.target_property_set} already has a hotel."
        else:
            return False, f"Validation Error: Unknown building type: m{building_type}"
            
        return True, None
    
    @staticmethod
    def _validate_move_property(action: Action) -> Tuple[bool, Optional[str]]:
        # No support for moving building cards
        if action.card.get_card_type() == CardType.ACTION_BUILDING:
            return False, "Validation Error: Moving buildings is not supported."

        if len(action.target_player_names) > 0:
            return False, f"Validation Error: Move Property should not specify target players. {action}"

        if action.target_property_set is None:
            return False, f"Validation Error: Move Property must specify a target property set. {action}"

        if action.rent_color is not None or action.double_the_rent_count:
            return False, f"Validation Error: Move Property should not specify rent related fields. {action}"

        if action.card.get_card_type() != CardType.PROPERTY_WILD:
            return False, f"Validation Error: Only wild property cards can be moved. {action.card.name}"

        # Ensure the player actually owns this card in properties
        found = False
        for prop_set in action.source_player.get_property_sets().values():
            if action.card in prop_set.cards:
                found = True
                break
        if not found:
            return False, f"Validation Error: Player does not own property {action.card.name}."

        if isinstance(action.card, WildPropertyCard):
            if action.target_property_set not in action.card.available_colors:
                return False, f"Validation Error: Wild card {action.card.name} cannot represent {action.target_property_set}."
        
        return True, None

    @staticmethod
    def _validate_pass_go(action: Action) -> Tuple[bool, Optional[str]]:
        if len(action.target_player_names) > 0:
            return False, f"Validation Error: Pass Go cannot have target players. {action}"
        if action.target_property_set is not None:
            return False, f"Validation Error: Pass Go cannot have target property set. {action}"
        if action.rent_color is not None:
            return False, f"Validation Error: Pass Go cannot have rent color. {action}"
        return True, None
    
    @staticmethod
    def _validate_birthday(action: Action) -> Tuple[bool, Optional[str]]:
        # relax birthday target player checking
        # if len(action.target_player_names) > 0:
        #     print(f"Validation Error: Birthday cannot target a specific player. {action}")
        #     return False
        if action.target_property_set is not None:
            return False, f"Validation Error: Birthday cannot have target property set. {action}"
        if action.rent_color is not None:
            return False, f"Validation Error: Birthday cannot have rent color. {action}"
        return True, None
    
    @staticmethod
    def _validate_debt_collector(action: Action) -> Tuple[bool, Optional[str]]:
        if len(action.target_player_names) != 1:
            return False, f"Validation Error: Debt Collector must have exactly one target player. Found {action}"
        if action.target_property_set is not None:
            return False, f"Validation Error: Debt Collector cannot have target property set. {action}"
        if action.rent_color is not None:
            return False, f"Validation Error: Debt Collector cannot have rent color. {action}"
        return True, None
    
    @staticmethod
    def _validate_deal_breaker(action: Action, player: Player, target_players: List[Player]) -> Tuple[bool, Optional[str]]:
        if len(target_players) != 1:
            return False, f"Validation Error: Deal Breaker must have exactly one target player. Found {action}"
        if action.target_property_set is None:
            return False, f"Validation Error: Deal Breaker must have target property set. {action}"
        target_property_set = target_players[0].get_property_sets().get(action.target_property_set)
        if target_property_set is None:
            return False, f"Validation Error: Deal Breaker target property set not found. {action}"
        if not target_property_set.is_full_set:
            return False, f"Validation Error: Deal Breaker can only steal full set. {action}"
        if action.rent_color is not None:
            return False, f"Validation Error: Deal Breaker cannot have rent color. {action}"
        
        return True, None
    
    @staticmethod
    def _validate_sly_deal(action: Action, player: Player, target_players: List[Player]) -> Tuple[bool, Optional[str]]:
        if len(target_players) != 1:
            return False, f"Validation Error: Sly Deal must have exactly one target player. Found {action}"
        if not target_players[0].has_card(action.forced_or_sly_deal_target_property_info.name):
            return False, f"Validation Error: Sly Deal target property not found in target player. {action}"
        target_property_set = None
        for color, prop_set in target_players[0].get_property_sets().items():
            if prop_set.has_card(action.forced_or_sly_deal_target_property_info.name):
                target_property_set = prop_set
                break
        if target_property_set is None:
            return False, f"Validation Error: Sly Deal target property set not found. {action}"
        if target_property_set.is_full_set:
            return False, f"Validation Error: Sly Deal cannot steal from full set. {action}"
        if action.rent_color is not None:
            return False, f"Validation Error: Sly Deal cannot have rent color. {action}"
        return True, None
    
    @staticmethod
    def _validate_forced_deal(action: Action, player: Player, target_players: List[Player]) -> Tuple[bool, Optional[str]]:
        if len(target_players) != 1:
            return False, f"Validation Error: Forced Deal must have exactly one target player. Found {action}"
        target_property_card = target_players[0].get_card_from_properties(action.forced_or_sly_deal_target_property_info)
        if target_property_card is None:
            return False, f"Validation Error: Forced Deal target property not found in target player. {action}"
        source_property_card = player.get_card_from_properties(action.forced_deal_source_property_info)
        if source_property_card is None:
            return False, f"Validation Error: Forced Deal source property not found in source player. {action}"
        target_property_set = target_players[0].get_property_sets().get(target_property_card.get_color())
        if target_property_set is None:
            return False, f"Validation Error: Forced Deal target property set not found. {action}"
        if target_property_set.is_full_set:
            return False, f"Validation Error: Forced Deal cannot steal from full set. {action}"
        if action.rent_color is not None:
            return False, f"Validation Error: Forced Deal cannot have rent color. {action}"
        return True, None
    
    @staticmethod
    def _validate_just_say_no(action: Action) -> Tuple[bool, Optional[str]]:
        return True, None
        

    @staticmethod
    def check_win_condition(player: Player) -> bool:
        """Checks if any player has met the win condition (3 full sets)."""
        property_sets = player.get_property_sets()
        win_set = set()
        for color, prop_set in property_sets.items():
            if prop_set.is_full_set:
                win_set.add(color)
        return len(win_set) >= 3
