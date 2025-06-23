import os
import json
import re
import requests
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from player import Player
from action import Action, ActionType, ActionPropertyInfo
from card import Card, PropertyColor, CardType
from deck_config import ACTIONS_PER_TURN
import sys 

load_dotenv()

class LLMHandler():
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.template_env = Environment(loader=FileSystemLoader('prompts'))

    @staticmethod
    def _extract_json(response):
        response = response.json()
        text = response['choices'][0]['message']['content']
        return json.loads(text)
        # return response

    def _render_template(self, template_name: str, **kwargs) -> str:
        """Render a Jinja2 template with the given context."""
        template = self.template_env.get_template(template_name)
        return template.render(**kwargs)
    
    def _get_structured_output_format(self, format):
        match format:
            case "action":
                json_template = {
                    "type": "json_schema",
                    "json_schema": {
                    "name": "play_action",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "reasoning": {
                                "type": "string",
                                "description": "Reasoning on what action you want to take."
                            },
                            "action_type": {
                                "type": "string",
                                "description": "The type of action you want to take. One of ADD_TO_BANK, ADD_TO_PROPERTIES, MOVE_PROPERTY, PLAY_ACTION, PASS"
                            },
                            "card_name": {
                                "type": "string",
                                "description": "(optional field) The name of the card to play, if necessary (should be exact)."
                            },  
                            "target_players": {
                                "type": "string",
                                "description": "(optional field) List of player names to target in python list format (e.g. ['Alice', 'Bob']) if necessary"
                            },
                            "target_property_set": {
                                "type": "string",
                                "description": "(optional field) The color name of the property set to target (or move to) if necessary"
                            },
                            "rent_color": {
                                "type": "string",
                                "description": "(optional field) The color to charge rent for (must be a valid color for the Rent card) if necessary"
                            },
                            "double_the_rent_count": {
                                "type": "integer",
                                "description": "(optional field) Number of Double the Rent cards to play with a Rent card (each consumes an action) if necessary"
                            },
                            "forced_deal_source_property_info": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "The name of the card from your properties to trade with the other player (should be exact)"
                                    },
                                    "prop_color": {
                                        "type": "string",
                                        "description": "The color of the property set to trade the card from"
                                    }
                                },
                                "required": ["name", "prop_color"],
                                "additionalProperties": False
                            },
                            "forced_or_sly_deal_target_property_info": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "The name of the card to steal from the target player (should be exact)"
                                    },
                                    "prop_color": {
                                        "type": "string",
                                        "description": "The color of the property set that the target player's card belongs to"
                                    }
                                },
                                "required": ["name", "prop_color"],
                                "additionalProperties": False
                            }
                        },
                        "required": ["reasoning", "action_type", "card_name", "target_players", "target_property_set", "rent_color", "double_the_rent_count","forced_deal_source_property_info","forced_or_sly_deal_target_property_info"],
                        "additionalProperties": False
                    }
                }}
            case "discard":
                json_template = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "discard",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Reasoning on what cards you want to discard from your hand."
                                },
                                "card_names": {
                                    "type": "string",
                                    "description": "A list of card names to discard from your hand (names should be exact)."
                                }
                            },
                            "required": ["reasoning", "card_names"],
                            "additionalProperties": False
                        }
                    }
                }
        return json_template

    def call_llm(self, template_name: str, response_format: str, **template_kwargs) -> Dict[str, Any]:
        """Call the LLM with a rendered template."""
        prompt = self._render_template(template_name, **template_kwargs)
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        }

        game_rules = self._render_template("game_rules.j2")
        system_message = {
            "role": "system",
            "content": game_rules,
        }
        payload = {
            "model": self.model_name,
            "messages": [system_message, {"role": "user", "content": prompt}],
            "temperature": 0.7,
            "response_format": self._get_structured_output_format(response_format),
            "structured_outputs": True,
            # "max_tokens": 1000
        }
        try:
            response = requests.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            sys.exit()
        return self._extract_json(response)



class LLMPlayer(Player, LLMHandler):
    def __init__(self, model_name: str):
        Player.__init__(self, name=model_name)
        LLMHandler.__init__(self, model_name)
        self.model_name = model_name

    def get_action(self, game_state_dict: dict) -> Optional[Action]:
        """Get the next action from the LLM."""
        response = self.call_llm(
            'get_action_prompt.j2',
            response_format="action",
            player=self,
            game_state=game_state_dict,
            actions_per_turn=ACTIONS_PER_TURN
        )

        if not isinstance(response, dict):
            raise ValueError(f"LLM response is not json: {response}")
        if 'action_type' not in response:
            raise ValueError("LLM response missing 'action_type'")

        action_type_str = response['action_type']

        try:
            action_type = ActionType[action_type_str]
        except KeyError:
            raise ValueError(f"Invalid action_type '{action_type_str}'")

        card = None
        card_name = response.get('card_name')
        if action_type != ActionType.PASS:
            if not card_name:
                raise ValueError("'card_name' required for non-PASS actions")
            card = next((c for c in self.hand if c.name == card_name), None)
            if not card:
                raise ValueError(f"Card {card_name} not found in hand")

        def build_info(data):
            if not data:
                return None
            return ActionPropertyInfo(name=data['name'], prop_color=PropertyColor[data['prop_color']])

        double_the_rent_count = response.get('double_the_rent_count')
        if double_the_rent_count is None:
            double_the_rent_count = 0

        return Action(
            action_type=action_type,
            source_player=self,
            card=card,
            target_player_names=response.get('target_players', []),
            target_property_set=PropertyColor[response.get('target_property_set')] if response.get('target_property_set') else None,
            rent_color=response.get('rent_color'),
            double_the_rent_count=double_the_rent_count,
            forced_deal_source_property_info=build_info(response.get('forced_deal_source_property_info')),
            forced_or_sly_deal_target_property_info=build_info(response.get('forced_or_sly_deal_target_property_info'))
        )

    def choose_cards_to_discard(self, num_cards_to_discard: int, game_state_dict: dict) -> List[Card]:
        """Choose cards to discard using the LLM."""
        response = self.call_llm(
            'choose_cards_to_discard_prompt.j2',
            response_format="discard",
            player=self,
            game_state=game_state_dict,
            num_cards_to_discard=num_cards_to_discard
        )
        
        discarded_cards = []
        for card_name in response:
            card = next((c for c in self.hand if c.name == card_name), None)
            if card:
                discarded_cards.append(card)
                    
        return discarded_cards

    def provide_payment(self, reason: str, amount: int, game_state_dict: dict) -> List:
        """Provide payment using the LLM to choose which cards to use, returning (Card, source) tuples."""
        try:
            response = self.call_llm(
                'provide_payment_prompt.j2',
                response_format="payment",
                player=self,
                reason=reason,
                amount=amount,
                game_state=game_state_dict,
                actions_per_turn=ACTIONS_PER_TURN
            )
            
            # Response should be a list of dicts: {"name": ..., "source": ...}
            payment_cards = []
            for item in response:
                card_name = item.get("name")
                source = item.get("source")
                card = None
                if source == "bank":
                    card = next((c for c in self.bank if c.name == card_name), None)
                elif source == "properties":
                    # Search all property sets
                    for prop_set in self.property_sets.values():
                        card = next((c for c in prop_set.cards if c.name == card_name), None)
                        if card:
                            break
                if card:
                    payment_cards.append((card, source))
                else:
                    print(f"Warning: Card '{card_name}' with source '{source}' not found in player's {source}.")
            return payment_cards
        except Exception as e:
            print(f"Exception. Error in provide_payment: {e}")
            return None

    def wants_to_negate(self, action: Action, game_state_dict: dict) -> bool:
        """Determine if the player wants to negate an action with a Just Say No card."""
        # Check if we have a Just Say No card
        just_say_no_count = len([c for c in self.hand if c.get_card_type() == CardType.ACTION_JUST_SAY_NO])
        if not just_say_no_count:
            return None
            
        try:
            response = self.call_llm(
                'wants_to_negate_prompt.j2',
                player=self,
                action=str(action),
                game_state=game_state_dict,
                actions_per_turn=ACTIONS_PER_TURN
            )
            
            return response.get('negate', False)
            
        except Exception as e:
            print(f"Error in wants_to_negate: {e}")
            return None

qwen3_235b = LLMPlayer(model_name="qwen/qwen3-235b-a22b:free")
deepseek_r1_0528 = LLMPlayer(model_name="deepseek/deepseek-r1-0528:free")
sarvam_m = LLMPlayer(model_name="sarvamai/sarvam-m:free")
meta_maverick = LLMPlayer(model_name="meta-llama/llama-4-maverick:free")
deepseek_v3_base = LLMPlayer(model_name="deepseek/deepseek-v3-base:free")
gemma3_27b = LLMPlayer(model_name="google/gemma-3-27b-it:free")
gemini_2_5_pro_experimental = LLMPlayer(model_name="google/gemini-2.5-pro-exp-03-25") #think its free?
gpt_4_1_nano = LLMPlayer(model_name="openai/gpt-4.1-nano-2025-04-14")
gpt_4_1_mini = LLMPlayer(model_name="openai/gpt-4.1-mini-2025-04-14")

if __name__ == "__main__":

    handler = LLMHandler(model_name="openai/gpt-4.1-mini-2025-04-14")
    handler.call_llm("test.j2", response_format="action")