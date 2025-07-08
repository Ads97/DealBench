import random
from typing import List, Optional, Dict, Any
from deck import Deck
from player import Player
from card import BuildingCard, Card, MoneyCard, PropertyCard, WildPropertyCard, RentCard, CardType, PropertyColor, PassGoCard, ItsMyBirthdayCard, DebtCollectorCard, DealBreakerCard, SlyDealCard, ForcedDealCard
from action import Action, ActionType, ActionPropertyInfo
from rules_engine import RulesEngine
import json
from deck_config import INITIAL_HAND_SIZE, MAX_HAND_SIZE, ACTIONS_PER_TURN, DRAWS_PER_TURN, PASS_GO_DRAW_COUNT, BIRTHDAY_GIFT_AMOUNT, DEBT_COLLECTOR_AMOUNT
from llm import qwen3_235b, deepseek_r1, meta_maverick, gpt_4_1_nano, claude_4_sonnet, openai_o4_mini, openai_o3, gemini_2_5_pro
import logging 
import time
import os 
logger = logging.getLogger(__name__)

class Game:
    """Orchestrates the Monopoly Deal game flow."""

    def __init__(self, players: List[Player]):
        """
        Initializes the game with a list of players.

        Args:
            players: A list of Player objects participating in the game.
        """
        if not players or len(players) < 2 or len(players) > 5:
            raise ValueError("Game requires between 2 and 5 players.")

        self.game_history = []
        logger.info("Initializing Game...")
        # 1. Create and shuffle the deck
        self.deck: Deck = Deck() 
        logger.info(f"Created deck with {self.deck.total_cards} cards.")
        random.shuffle(players)
        self.players = players
        self.add_to_game_history(f"Play order: {', '.join([p.name for p in players])}")

        # 4. Initialize Action Handler
        self.rules_engine = RulesEngine()

        # 5. Deal initial hands
        self.add_to_game_history(f"Dealing initial {INITIAL_HAND_SIZE} cards to each player...")
        for player in self.players:
            for _ in range(INITIAL_HAND_SIZE):
                card = self.deck.draw_card()
                player.add_card_to_hand(card)
        
        self.game_winner = None
        player_names_for_file = "_".join([p.name.replace("/", "_") for p in self.players])
        self.game_identifier = f"{time.strftime('%Y-%m-%d_%H-%M-%S')}_{player_names_for_file}_game"
        logger.info("Initial hands dealt.")

        logger.info("Game Setup Complete.")

    def add_to_game_history(self, message: str, debug=False):
        if debug:
            logger.info(message)
        self.game_history.append(message)
    
    def save_game(self):
        things_to_save = {
            "game_history": self.game_history,
            "players": [p.to_json(debug=True) for p in self.players],
            "game_state": self.to_json(debug=True),
            "winner": self.game_winner,
            "turn_count": self.turn_count,
        }
        with open(f"logs/{self.game_identifier}/result.json", "w") as f:
            json.dump(things_to_save, f, indent=4)
    
    def run_game(self):
        """Runs the main game loop until a winner is determined."""
        self.add_to_game_history("\n--- Starting Game --- ")
        self.turn_count = 0
        while self.game_winner is None:
            current_player = self._get_current_player()
            self.add_to_game_history(f"\n--- {current_player.name}'s Turn ---")
            self._take_turn(current_player)
            has_won = self.rules_engine.check_win_condition(current_player)
            if has_won:
                self.game_winner = current_player.name
                self.add_to_game_history(f"\n--- GAME OVER --- {self.game_winner} wins! ---")
                break
            self.turn_count += 1

        if self.game_winner:
            self.add_to_game_history(f"{self.game_winner} is the winner after {self.turn_count} turns!")
            self.save_game()

    def _get_current_player(self):
        return self.players[self.turn_count%len(self.players)]
        
    def _take_turn(self, player: Player):
        """Handles the logic for a single player's turn."""
        self.add_to_game_history(f"{player.name} starts turn.")
        # print(json.dumps(self.to_json(debug=True), indent=4))
        # draw two cards first 
        for _ in range(DRAWS_PER_TURN):
            card = self.deck.draw_card()
            player.add_card_to_hand(card)
        
        # now play up to 3 actions
        self.actions_played = 0
        while self.actions_played < ACTIONS_PER_TURN:
            # TODO: Display game state to player (hand, properties, bank etc.)
            self.add_to_game_history(f"{player.name} has played {self.actions_played}/{ACTIONS_PER_TURN} actions.")

            valid = False
            error_reason = None
            attempts = 0
            while not valid and attempts < 2:
                if error_reason:
                    logger.info(f"Invalid action chosen: {error_reason}. Trying again.")
                try:
                    action = player.get_action(self.to_json(), self.game_history)
                    target_players = [self._get_player_by_name(n) for n in action.target_player_names]
                    valid, error_reason = self.rules_engine.validate_action(action, player, target_players, self.actions_played)
                    attempts += 1
                except Exception as e:
                    error_reason = f"Error in getting action from player {player.name}! Exception: {e}"
                    valid = False
                    continue
            
            if not valid:
                self.add_to_game_history(f"Skipping {player.name}'s action due to invalid actions: {error_reason}")
                break

            if action.action_type == ActionType.PASS: # Player chose to end turn
                self.add_to_game_history(f"{player.name} has chosen to end their action phase.")
                break

            # now execute action
            successfully_executed = self.execute(action)
            if action.action_type != ActionType.MOVE_PROPERTY:
                self.actions_played += 1  # Move property does not count towards actions per turn
            if successfully_executed:
                logger.info(f"Action successful: {action}")
            else:
                logger.info(f"Could not execute action: {action}")
            has_won = self.rules_engine.check_win_condition(player)
            if has_won:
                    self.game_winner = player
                    return  # End turn immediately if someone won

        # 3. Discard excess cards
        if player.cards_in_hand > MAX_HAND_SIZE:
            num_cards_to_discard = player.cards_in_hand - MAX_HAND_SIZE
            self.add_to_game_history(f"{player.name} has more than {MAX_HAND_SIZE} cards! Discard {num_cards_to_discard} cards")
            cards_to_discard = player.choose_cards_to_discard(num_cards_to_discard, self.to_json(), self.game_history)
            # TODO: Separate out the functions where a player chooses what to do, and the functions that control player state?
            for card in cards_to_discard:
                self.add_to_game_history(f"{player.name} discards {card}")
                player.remove_card_from_hand(card)
            if player.cards_in_hand > MAX_HAND_SIZE:
                raise ValueError(f"Player {player.name} still has {player.cards_in_hand} cards in hand. player hand: {player.hand}")

        self.add_to_game_history(f"{player.name} ends turn.")

    def to_json(self, debug=False) -> Dict[str, Any]:
        """Exposes all the game state that a player should have access to."""
        json_state = {
            "current_player_name": self._get_current_player().name,
            "turns_completed_in_game": self.turn_count,
            "actions_played_in_current_turn": self.actions_played,
            "players": [player.to_json(debug) for player in self.players],
        }
        return json_state

    def _get_player_by_name(self, name: str) -> Optional[Player]:
        """Finds the Player object corresponding to a name."""
        for player in self._get_all_players():
            if player.name == name:
                return player
        return None

    def _get_all_players(self) -> List[Player]:
        """Placeholder to get the list of Player objects."""
        return self.players 

    def execute(self, action: Action) -> bool:
        """Handle playing an action card."""
        # Assuming Card object has a method like is_action() or check type
        # if not self.card.is_action(): 
        #     raise ValueError(f"Card {self.card.name} is not an action card.")

        # Remove card from player's hand and add to discard pile
        if action.action_type != ActionType.MOVE_PROPERTY:
            action.source_player.remove_card_from_hand(action.card)
            self.deck.discard_card(action.card) # Assuming game has discard_pile with add method

        action_type = action.action_type

        match action_type:
            case ActionType.ADD_TO_BANK:
                return self._execute_add_to_bank(action)
            case ActionType.ADD_TO_PROPERTIES:
                return self._execute_add_to_properties(action)
            case ActionType.MOVE_PROPERTY:
                return self._execute_move_property(action)
            case ActionType.PASS:
                return self._execute_pass(action)
            case ActionType.PLAY_ACTION:
                return self._execute_action(action)
            case _:
                raise ValueError(f"Unexpected action type: {action_type}")

    def _execute_add_to_bank(self, action: Action):
        """Handle playing a money card to the bank."""
        player = action.source_player
        card = action.card
        
        player.add_card_to_bank(card)
        self.add_to_game_history(f"{player.name} banked ${card.value}M")
        return True

    def _execute_add_to_properties(self, action: Action):
        """Handle playing a standard property card to the table."""
        player = action.source_player
        card = action.card
        
        if isinstance(card, WildPropertyCard):
            card.current_color = action.target_property_set
        if isinstance(card, PropertyCard):
            player.add_card_to_properties(card)
        elif isinstance(card, BuildingCard):
            player.add_card_to_properties(card, action.target_property_set)
        self.add_to_game_history(f"{player.name} added property {card.name} to {action.target_property_set}")
        return True    
    
    def _execute_move_property(self, action: Action):
        """Handle moving a property card to a different set."""
        player = action.source_player
        card = action.card
        target_property_set = action.target_property_set
        
        player.remove_card_from_properties(card)
        player.add_card_to_properties(card, target_property_set)

        self.add_to_game_history(f"{player.name} moved property {card.name} to {target_property_set}")
        return True

    def _execute_pass(self, action):
        raise ValueError("Pass action should not be executed.")

    def _execute_action(self, action):
        """Handle playing an action card."""
        match action.card.get_card_type():
            case CardType.ACTION_RENT:
                return self._execute_action_rent(action)
            case CardType.ACTION_BUILDING:
                return self._execute_add_to_properties(action)
            case CardType.ACTION_PASS_GO:
                return self._execute_pass_go(action)
            case CardType.ACTION_BIRTHDAY:
                return self._execute_its_my_birthday(action)
            case CardType.ACTION_DEBT_COLLECTOR:
                return self._execute_debt_collector(action)
            case CardType.ACTION_DEAL_BREAKER:
                return self._execute_deal_breaker(action)
            case CardType.ACTION_SLY_DEAL:
                return self._execute_sly_deal(action)
            case CardType.ACTION_FORCED_DEAL:
                return self._execute_forced_deal(action)
            case _:
                raise ValueError(f"Unexpected action type: {action.card.get_card_type()}")
    
    def _get_money_from(self, source_player: Player, target_player: Player, amount: int, reason: str):
        if amount==0:
            return True
        if self._attempt_just_say_no(f"collect {amount} for {reason}", source_player, target_player):
            self.add_to_game_history(f"{target_player.name}'s Just Say No cancelled the {reason} request from {source_player.name}.")
            return False
        payment_cards = target_player.provide_payment(reason=reason,amount=amount, game_state_dict=self.to_json(), game_history=self.game_history)
        valid, reason_msg = self.rules_engine.validate_rent_payment(payment_cards)
        attempts = 0
        while not valid and attempts < 2:
            logger.error(f"Invalid payment: {reason_msg}. Trying again.")
            payment_cards = target_player.provide_payment(reason=reason,amount=amount, game_state_dict=self.to_json(), game_history=self.game_history)
            valid, reason_msg = self.rules_engine.validate_rent_payment(payment_cards)
            attempts += 1
        if not valid:
            self.add_to_game_history(f"Skipping payment due to invalid inputs: {reason_msg}")
            return False
        actual_amount_paid = sum(card.value for card, _ in payment_cards)
        self.add_to_game_history(f"{target_player.name} paid {actual_amount_paid}M ({amount}M requested) to {source_player.name} with cards {payment_cards} for {reason}.")
        for card, source in payment_cards:
            source_player.add_card(card, source)
            target_player.remove_card(card, source)
        return True

    def _execute_action_rent(self, action: Action): #TODO: handle double the rent
        """Handle playing a rent card."""
        player = action.source_player
        card = action.card
        property_sets = player.get_property_sets()
        rent_value = property_sets[action.rent_color].get_rent_value()
        if action.double_the_rent_count:
            rent_value = rent_value * 2**action.double_the_rent_count
            player.remove_double_rent_card_from_hand()
        
        # Charge rent to other players
        if not card.is_wild:
            success = []
            for other_player in self._get_all_players():
                if other_player != player:
                    success.append(self._get_money_from(player, other_player, rent_value, "rent"))
            return any(success)
        else:
            target_player_name = action.target_player_names[0]
            target_player = self._get_player_by_name(target_player_name)
            if target_player is None:
                raise ValueError(f"Target player {target_player_name} not found.")
            return self._get_money_from(player, target_player, rent_value, "rent")
    
    def _execute_pass_go(self, action: Action):
        player = action.source_player
        for _ in range(PASS_GO_DRAW_COUNT):
            card = self.deck.draw_card()
            player.add_card_to_hand(card)
        self.add_to_game_history(f"{player.name} received {PASS_GO_DRAW_COUNT} cards from Pass Go. {player.name} now has {player.cards_in_hand} cards.")
        return True

    def _execute_its_my_birthday(self, action: Action):
        player = action.source_player
        success = []
        for other_player in self._get_all_players():
            if other_player != player:
                success.append(self._get_money_from(player, other_player, BIRTHDAY_GIFT_AMOUNT, "birthday"))
        return any(success)
        
    
    def _execute_debt_collector(self, action: Action):
        player = action.source_player
        target_player_name = action.target_player_names[0]
        target_player = self._get_player_by_name(target_player_name)
        if target_player is None:
            raise ValueError(f"Target player {target_player_name} not found for action {action}.")
        return self._get_money_from(player, target_player, DEBT_COLLECTOR_AMOUNT, "debt collection")
    
    def _execute_deal_breaker(self, action: Action):
        player = action.source_player
        target_player_name = action.target_player_names[0]
        target_player = self._get_player_by_name(target_player_name)
        if target_player is None:
            raise ValueError(f"Target player {target_player_name} not found for action {action}.")
        if self._attempt_just_say_no(f"deal breaker - steal property set {action.target_property_set}", player, target_player):
            self.add_to_game_history(f"{target_player.name} cancelled the Deal Breaker from {player.name} with Just Say No.")
            return False
        set_color = action.target_property_set
        property_set = target_player.remove_property_set(set_color)
        player.add_property_set(set_color, property_set)
        self.add_to_game_history(f"{player.name} stole property set {set_color} from {target_player_name} with a deal breaker.")
        return True
    
    def _execute_sly_deal(self, action: Action):
        player = action.source_player
        target_player_name = action.target_player_names[0]
        target_player = self._get_player_by_name(target_player_name)
        if target_player is None:
            raise ValueError(f"Target player {target_player_name} not found for action {action}.")
        if self._attempt_just_say_no(f"sly deal - steal property {action.forced_or_sly_deal_target_property_info.name}", player, target_player):
            self.add_to_game_history(f"{target_player.name} cancelled the Sly Deal from {player.name} with Just Say No.")
            return False
        stolen_card = target_player.get_card_from_properties(action.forced_or_sly_deal_target_property_info)
        target_player.remove_card_from_properties(stolen_card)
        player.add_card_to_properties(stolen_card)
        self.add_to_game_history(f"{player.name} stole property {stolen_card.name} from {target_player_name} with a sly deal.")
        return True
        
    def _execute_forced_deal(self, action: Action):
        player = action.source_player
        target_player_name = action.target_player_names[0]
        target_player = self._get_player_by_name(target_player_name)
        if target_player is None:
            raise ValueError(f"Target player {target_player_name} not found for action {action}.")
        if self._attempt_just_say_no(f"forced deal - take away {action.forced_or_sly_deal_target_property_info.name} and receive {action.forced_deal_source_property_info.name}", player, target_player):
            self.add_to_game_history(f"{target_player.name} cancelled the Forced Deal from {player.name} with Just Say No.")
            return False
        source_card = player.get_card_from_properties(action.forced_deal_source_property_info)
        target_card = target_player.get_card_from_properties(action.forced_or_sly_deal_target_property_info)
        player.remove_card_from_properties(source_card)
        target_player.add_card_to_properties(source_card)
        target_player.remove_card_from_properties(target_card)
        player.add_card_to_properties(target_card)
        self.add_to_game_history(f"{player.name} forced deal {source_card.name} to {target_player_name} and received {target_card.name}.")
        return True

    def _attempt_just_say_no(self, reason: str, source_player: Player, target_player: Player) -> bool:
        """Handle a possible chain of Just Say No cards.

        Returns True if the pending action should be cancelled."""
        current = target_player
        other = source_player
        jsn_played = False

        action_chain_str = f"{source_player.name} has just performed action '{reason}' on {target_player.name}."

        while True:
            valid = False
            attempts = 0
            while not valid and attempts < 3:
                if attempts:
                    logger.error(f"Invalid Just Say No action: {reason}. Trying again.")
                action = current.wants_to_negate(action_chain_str=action_chain_str, target_player_name=other.name, game_state_dict=self.to_json(), game_history=self.game_history)
                valid, reason = self.rules_engine.validate_action(action, current, [other], None)
                attempts += 1

            if not valid:
                self.add_to_game_history("Skipping Just Say No due to invalid inputs.")
                break
            if not action:
                break
            current.remove_card_from_hand(action.card)
            self.add_to_game_history(f"{current.name} played Just Say No!")
            action_chain_str += f"\n{current.name} played Just Say No!"
            jsn_played = True
            current, other = other, current

        return jsn_played and current == source_player    
        

class TestPlayer(Player):
    def get_action(self, game_state_dict: dict, game_history: List[str]) -> Optional[Action]:
        """
        Build a list of every *legal* move the player can make in the current
        state, then pick one uniformly at random.  
        Falls back to a PASS action if nothing is available.
        """
        valid_actions: list[Action] = []

        # Pre‑compute data that several cards may need
        property_sets         = self.get_property_sets()
        my_property_colors    = list(property_sets.keys())
        other_player_names    = [p["name"] for p in game_state_dict["players"] if p["name"] != self.name]
        double_the_rent_count = sum(
            1 for c in self.hand if getattr(c, "get_card_type", lambda: None)() == CardType.ACTION_DOUBLE_THE_RENT
        )
        double_the_rent_count = min(double_the_rent_count, ACTIONS_PER_TURN -game_state_dict['actions_played_in_current_turn'] - 1)

        for card in self.hand:

            # --- Money ----------------------------------------------------------
            if isinstance(card, MoneyCard):
                valid_actions.append(
                    Action(source_player=self, card=card,
                        action_type=ActionType.ADD_TO_BANK)
                )

            # --- Wild property --------------------------------------------------
            elif isinstance(card, WildPropertyCard):
                for color in card.available_colors:
                    valid_actions.append(
                        Action(source_player=self, card=card,
                            action_type=ActionType.ADD_TO_PROPERTIES,
                            target_property_set=color)
                    )

            # --- Standard property ---------------------------------------------
            elif isinstance(card, PropertyCard):
                valid_actions.append(
                    Action(source_player=self, card=card,
                        action_type=ActionType.ADD_TO_PROPERTIES)
                )
            
            elif isinstance(card, BuildingCard):
                full_sets = [(color, property_set) for color, property_set in property_sets.items() if property_set.is_full_set]
                if full_sets:
                    if card.building_type == "house":
                        for color, property_set in full_sets:
                            if not (property_set.has_house or color in (PropertyColor.RAILROAD, PropertyColor.UTILITY)):
                                valid_actions.append(
                                    Action(source_player=self, card=card,
                                        action_type=ActionType.PLAY_ACTION,
                                        target_property_set=color)
                                )
                    elif card.building_type == "hotel":
                        for color, property_set in full_sets:
                            if property_set.has_house and not property_set.has_hotel:
                                valid_actions.append(
                                    Action(source_player=self, card=card,
                                        action_type=ActionType.PLAY_ACTION,
                                        target_property_set=color)
                                )

            # --- Rent card ------------------------------------------------------
            elif isinstance(card, RentCard) and my_property_colors:
                if not card.is_wild:
                    # Coloured rent card
                    for color in my_property_colors:
                        if color in card.colors:
                            valid_actions.append(
                                Action(source_player=self, card=card,
                                    action_type=ActionType.PLAY_ACTION,
                                    rent_color=color,
                                    double_the_rent_count=double_the_rent_count)
                            )
                else:
                    # Wild rent card: can pick any colour + any single opponent
                    for color in my_property_colors:
                        for target in other_player_names:
                            valid_actions.append(
                                Action(source_player=self, card=card,
                                    action_type=ActionType.PLAY_ACTION,
                                    rent_color=color,
                                    target_player_names=[target],
                                    double_the_rent_count=double_the_rent_count)
                            )
            elif isinstance(card, PassGoCard):
                valid_actions.append(
                    Action(source_player=self, card=card,
                        action_type=ActionType.PLAY_ACTION)
                )
            
            elif isinstance(card, ItsMyBirthdayCard):
                valid_actions.append(
                    Action(source_player=self, card=card,
                        action_type=ActionType.PLAY_ACTION)
                )
            
            elif isinstance(card, DebtCollectorCard):
                target_player = random.choice(other_player_names)
                valid_actions.append(
                    Action(source_player=self, card=card,target_player_names=[target_player],
                        action_type=ActionType.PLAY_ACTION)
                )
            
            elif isinstance(card, DealBreakerCard):
                for target_player in game_state_dict['players']:
                    if target_player['name'] == self.name:
                        continue
                    for color, set in target_player['property_sets'].items():
                        if set['is_full_set']:
                            valid_actions.append(
                                Action(source_player=self, card=card,target_player_names=[target_player['name']],
                                    action_type=ActionType.PLAY_ACTION,
                                    target_property_set=PropertyColor[color])
                            )
            elif isinstance(card, SlyDealCard):
                for target_player in game_state_dict['players']:
                    if target_player['name'] == self.name:
                        continue
                    for color, set in target_player['property_sets'].items():
                        if not set['is_full_set']:
                            property_cards = [c for c in set['cards'] if 'set_color' in c or 'current_color' in c]
                            card_choice = random.choice(property_cards)
                            color_key = card_choice.get('set_color') or card_choice.get('current_color')
                            target_info = ActionPropertyInfo(name=card_choice['name'], prop_color=PropertyColor[color_key])
                            valid_actions.append(
                                Action(source_player=self, card=card,target_player_names=[target_player['name']],
                                    action_type=ActionType.PLAY_ACTION, forced_or_sly_deal_target_property_info=target_info)
                            )
            elif isinstance(card, ForcedDealCard):
                hand_properties = [card for prop_set in self.get_property_sets().values() for card in prop_set.cards if isinstance(card, PropertyCard)]
                if len(hand_properties) > 0:
                    source_property = random.choice(hand_properties)
                    for target_player in game_state_dict['players']:
                        if target_player['name'] == self.name:
                            continue
                        for color, set in target_player['property_sets'].items():
                            if not set['is_full_set']:
                                property_cards = [c for c in set['cards'] if 'set_color' in c or 'current_color' in c]
                                target_property = random.choice(property_cards)
                                target_color_key = target_property.get('set_color') or target_property.get('current_color')
                                source_info = ActionPropertyInfo(name=source_property.name, prop_color=source_property.get_color())
                                target_info = ActionPropertyInfo(name=target_property['name'], prop_color=PropertyColor[target_color_key])
                                valid_actions.append(
                                    Action(source_player=self, card=card,target_player_names=[target_player['name']],
                                        action_type=ActionType.PLAY_ACTION, forced_deal_source_property_info=source_info,
                                        forced_or_sly_deal_target_property_info=target_info)
                                )

        # ------------------------------------------------------------------------
        # Choose and return one action (or PASS if none are legal)
        # ------------------------------------------------------------------------
        if valid_actions:
            return random.choice(valid_actions)

        # TODO: Test move property action
        return Action(source_player=self, action_type=ActionType.PASS)
    
    
    def choose_cards_to_discard(self, num_cards_to_discard, game_state_dict, game_history: List[str]) -> List[Card]:
        cards_to_discard = random.sample(self.hand,num_cards_to_discard)
        return cards_to_discard
    
    def provide_payment(self, reason: str, amount: int, game_state_dict: dict, game_history: List[str]):
        bank_value = sum(card.value for card in self.bank)
        if bank_value >= amount:
            payment = []
            total = 0
            sorted_bank = sorted(self.bank, key=lambda x: x.value)
            for card in sorted_bank:
                payment.append((card, "bank"))
                total += card.value
                if total >= amount:
                    return payment
        else:   
            payment = [(card, "bank") for card in self.bank.copy()]
            total = bank_value
            sorted_properties = sorted(self.property_sets.values(), key=lambda x: x.total_value())
            for prop_set in sorted_properties:
                for card in prop_set.cards:
                    payment.append((card, "properties"))
                    total += card.value
                    if total >= amount:
                        return payment
        return payment
    
    def wants_to_negate(self, action_chain_str: str, target_player_name: str, game_state_dict: dict, game_history: List[str]) -> Optional[Action]:
        for card in self.hand:
            if card.get_card_type() == CardType.ACTION_JUST_SAY_NO:
                return Action(action_type=ActionType.PLAY_ACTION, source_player=self, card=card, target_player_names=[target_player_name])
        return None

def setup_logging(log_file_name: str):
    """Set up a dedicated logger for a single game.

    Each game in a tournament should log to its own file to avoid mixed log
    messages when multiple games run concurrently.  This function creates a
    new ``logging.Logger`` instance whose messages are written only to the
    specified log file and replaces the module level ``logger`` used
    throughout the code base.
    """

    global logger
    os.makedirs(f"logs/{log_file_name}", exist_ok=True)

    # Create a unique logger for this game and ensure it does not propagate to
    # the root logger (which may have handlers for other games).
    game_logger = logging.getLogger(log_file_name)
    game_logger.setLevel(logging.INFO)
    game_logger.propagate = False

    file_handler = logging.FileHandler(f"logs/{log_file_name}/prompts.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    # Remove any existing handlers so we don't accumulate handlers across games
    game_logger.handlers = []
    game_logger.addHandler(file_handler)

    logger = game_logger

    # Update loggers in other modules to use this game's logger as their parent
    import deck, deck_config, llm, player

    deck.logger = logger.getChild("deck")
    deck_config.logger = logger.getChild("deck_config")
    llm.logger = logger.getChild("llm")
    player.logger = logger.getChild("player")

    return logger

# Example Usage (Conceptual - requires other classes and deck_utils)
if __name__ == "__main__":
    players = [
        # TestPlayer(name="Alice"),
        # TestPlayer(name="Bob"),
        # meta_maverick,
        # gpt_4_1_nano,
        # deepseek_r1,
        # qwen3_235b,
        # claude_4_sonnet,
        # openai_o4_mini,
        openai_o3,
        gemini_2_5_pro
    ]
    assert len(players) == len(set([player.name for player in players])), "Player names should be unique!"
    game = Game(players)
    setup_logging(game.game_identifier)
    game.run_game()