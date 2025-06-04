from typing import Any, List, Optional, Tuple
from action import Action, ActionType
from card import CardType, PropertyColor, PropertyCard, RentCard, BuildingCard, ActionCard, Card, WildPropertyCard # etc.
from player import Player
from deck_config import ACTIONS_PER_TURN

class RulesEngine:
    @staticmethod
    def validate_action(action: Action, current_player: Player, target_players: List[Player], actions_played: Optional[int]) -> bool:
        """Validates if a proposed action is legal according to game rules."""
        print(f"Validating Action: {action}") # Debug print
        if not action.card:
            return False

        if action.source_player != current_player:
            return False

        # Check if player has the card (unless it's a context action like passing)
        if action.card not in action.source_player.hand:
            print(f"Validation Error: {action.source_player.name} does not have {action.card.name}")
            return False
        
        if not (action.action_type==ActionType.PLAY_ACTION and action.card.get_card_type() == CardType.ACTION_RENT):
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
            return RulesEngine._validate_action_card(action, current_player, target_players, actions_played)
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
    def _validate_action_card(action: Action, player: Player, target_players: List[Player], actions_played: int) -> bool:
        if action.card.get_card_type() not in (CardType.ACTION, CardType.ACTION_RENT, CardType.ACTION_BUILDING, CardType.ACTION_DOUBLE_THE_RENT, CardType.ACTION_JUST_SAY_NO, CardType.ACTION_PASS_GO, CardType.ACTION_BIRTHDAY, CardType.ACTION_DEAL_BREAKER, CardType.ACTION_SLY_DEAL, CardType.ACTION_FORCED_DEAL, CardType.ACTION_DEBT_COLLECTOR):
            return False
        
        if action.source_player.name in action.target_player_names:
            print("Validation Error: Action cards cannot target the player who played them.")
            return False
        
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
            print(f"Validation Error: Unknown building type: m{building_type}")
            return False
            
        return True
    
    @staticmethod
    def _validate_move_property(action: Action) -> bool:
        # No support for moving building cards
        if action.card.get_card_type() == CardType.ACTION_BUILDING:
            print("Validation Error: Moving buildings is not supported.")
            return False

        if len(action.target_player_names) > 0:
            print(f"Validation Error: Move Property should not specify target players. {action}")
            return False

        if action.target_property_set is None:
            print(f"Validation Error: Move Property must specify a target property set. {action}")
            return False

        if action.rent_color is not None or action.double_the_rent_count:
            print(f"Validation Error: Move Property should not specify rent related fields. {action}")
            return False

        if action.card.get_card_type() != CardType.PROPERTY_WILD:
            print(f"Validation Error: Only wild property cards can be moved. {action.card.name}")
            return False

        # Ensure the player actually owns this card in properties
        found = False
        for prop_set in action.source_player.get_property_sets().values():
            if action.card in prop_set.cards:
                found = True
                break
        if not found:
            print(f"Validation Error: Player does not own property {action.card.name}.")
            return False

        if isinstance(action.card, WildPropertyCard):
            if action.target_property_set not in action.card.available_colors:
                print(f"Validation Error: Wild card {action.card.name} cannot represent {action.target_property_set}.")
                return False

        return True

    @staticmethod
    def _validate_pass_go(action: Action) -> bool:
        if len(action.target_player_names) > 0:
            print(f"Validation Error: Pass Go cannot have target players. {action}")
            return False
        if action.target_property_set is not None:
            print(f"Validation Error: Pass Go cannot have target property set. {action}")
            return False
        if action.rent_color is not None:
            print(f"Validation Error: Pass Go cannot have rent color. {action}")
            return False
        return True
    
    @staticmethod
    def _validate_birthday(action: Action) -> bool:
        if len(action.target_player_names) > 0:
            print(f"Validation Error: Birthday cannot have target players. {action}")
            return False
        if action.target_property_set is not None:
            print(f"Validation Error: Birthday cannot have target property set. {action}")
            return False
        if action.rent_color is not None:
            print(f"Validation Error: Birthday cannot have rent color. {action}")
            return False
        return True
    
    @staticmethod
    def _validate_debt_collector(action: Action) -> bool:
        if len(action.target_player_names) != 1:
            print(f"Validation Error: Debt Collector must have exactly one target player. Found {action}")
            return False
        if action.target_property_set is not None:
            print(f"Validation Error: Debt Collector cannot have target property set. {action}")
            return False
        if action.rent_color is not None:
            print(f"Validation Error: Debt Collector cannot have rent color. {action}")
            return False
        return True
    
    @staticmethod
    def _validate_deal_breaker(action: Action, player: Player, target_players: List[Player]) -> bool:
        if len(target_players) != 1:
            print(f"Validation Error: Deal Breaker must have exactly one target player. Found {action}")
            return False
        if action.target_property_set is None:
            print(f"Validation Error: Deal Breaker must have target property set. {action}")
            return False
        target_property_set = target_players[0].get_property_sets().get(action.target_property_set)
        if target_property_set is None:
            print(f"Validation Error: Deal Breaker target property set not found. {action}")
            return False
        if not target_property_set.is_full_set:
            print(f"Validation Error: Deal Breaker can only steal full set. {action}")
            return False
        if action.rent_color is not None:
            print(f"Validation Error: Deal Breaker cannot have rent color. {action}")
            return False
        
        return True
    
    @staticmethod
    def _validate_sly_deal(action: Action, player: Player, target_players: List[Player]) -> bool:
        if len(target_players) != 1:
            print(f"Validation Error: Sly Deal must have exactly one target player. Found {action}")
            return False
        if action.target_property_set is not None:
            print(f"Validation Error: Sly Deal should not specify target property set. {action}")
            return False
        if not target_players[0].has_card(action.forced_or_sly_deal_target_property_name): # TODO fix 
            print(f"Validation Error: Sly Deal target property not found in target player. {action}")
            return False 
        target_property_set = None
        for color, prop_set in target_players[0].get_property_sets().items():
            if prop_set.has_card(action.forced_or_sly_deal_target_property_name):
                target_property_set = prop_set
                break
        if target_property_set is None:
            print(f"Validation Error: Sly Deal target property set not found. {action}")
            return False
        if target_property_set.is_full_set:
            print(f"Validation Error: Sly Deal cannot steal from full set. {action}")
            return False
        if action.rent_color is not None:
            print(f"Validation Error: Sly Deal cannot have rent color. {action}")
            return False
        return True
    
    @staticmethod
    def _validate_forced_deal(action: Action, player: Player, target_players: List[Player]) -> bool:
        if len(target_players) != 1:
            print(f"Validation Error: Forced Deal must have exactly one target player. Found {action}")
            return False
        if action.target_property_set is not None:
            print(f"Validation Error: Forced Deal should not specify target property set. {action}")
            return False
        target_property_card = target_players[0].get_card_from_properties(action.forced_or_sly_deal_target_property_name)
        if target_property_card is None:
            print(f"Validation Error: Forced Deal target property not found in target player. {action}")
            return False
        source_property_card = player.get_card_from_properties(action.forced_deal_source_property_name)
        if source_property_card is None:
            print(f"Validation Error: Forced Deal source property not found in source player. {action}")
            return False
        target_property_set = target_players[0].get_property_sets().get(target_property_card.get_color())
        if target_property_set is None:
            print(f"Validation Error: Forced Deal target property set not found. {action}")
            return False
        if target_property_set.is_full_set:
            print(f"Validation Error: Forced Deal cannot steal from full set. {action}")
            return False
        if action.rent_color is not None:
            print(f"Validation Error: Forced Deal cannot have rent color. {action}")
            return False
        return True
    
    @staticmethod
    def _validate_just_say_no(action: Action) -> bool:
        if len(action.target_player_names) != 1:
            print(f"Validation Error: Just Say No must target exactly one player. {action}")
            return False
        if action.target_property_set is not None or action.rent_color is not None:
            print(f"Validation Error: Just Say No should not specify property set or rent color. {action}")
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
