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
from requests.exceptions import RequestException
import time 
import logging
logger = logging.getLogger(__name__)

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
        reasoning = response['choices'][0]['message']['reasoning']
        logger.info(f"=== LLM REASONING === \n{reasoning}\n===END LLM REASONING===")
        logger.info(f"=== LLM OUTPUT === \n{text}\n===END LLM OUTPUT===")
        return json.loads(text)
        # return response

    def _render_template(self, template_name: str, **kwargs) -> str:
        """Render a Jinja2 template with the given context."""
        template = self.template_env.get_template(template_name)
        return template.render(**kwargs)
    
    def _get_structured_output_format(self, format, **kwargs):
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
                                "description": "(optional field) The name of the card to play, if necessary (should be exact). Null if not needed"
                            },  
                            "target_players": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "description": "The name of the player to target (should be exact)."
                                },
                            },
                            "target_property_set": {
                                "type": "string",
                                "description": "(optional field) The color name of the property set to target (or move to) if necessary. Null otherwise"
                            },
                            "rent_color": {
                                "type": "string",
                                "description": "(optional field) The color to charge rent for (must be a valid color for the Rent card) if necessary. Null otherwise"
                            },
                            "double_the_rent_count": {
                                "type": "integer",
                                "description": "Number of Double the Rent cards (0-2) to play with a Rent card (each consumes an action) if necessary. 0 if not applicable"
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
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "description": "The name of the card to discard from your hand (name should be exact)."
                                    },
                                    "minItems": kwargs["num_cards_to_discard"],
                                    "maxItems": kwargs["num_cards_to_discard"],
                                }
                            },
                            "required": ["reasoning", "card_names"],
                            "additionalProperties": False
                        }
                    }
                }
            case "payment":
                json_template = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "provide_payment",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Reasoning on the cards you want to use to pay."
                                },
                                "payment": {
                                    "type": "array",
                                    "items":{
                                        "type": "object",
                                        "properties":{
                                            "card_name": {
                                                "type": "string",
                                                "description": "The name of the card to use to pay (name should be exact)."
                                            },
                                            "source": {
                                                "type": "string",
                                                "description": "Where the card belongs. One of 'bank' or 'properties'."
                                            }
                                        },
                                        "required": ["card_name", "source"],
                                        "additionalProperties": False
                                    },
                                }
                            },
                            "required": ["reasoning", "payment"],
                            "additionalProperties": False
                        }
                    }
                }
            case "negate":
                json_template = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "wants_to_negate",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "reasoning": {
                                    "type": "string",
                                    "description": "Reasoning on whether you want to play the just say no card"
                                },
                                "use_just_say_no": {
                                    "type": "boolean",
                                    "description": "Whether you want to play the just say no card"
                                }
                            },
                            "required": ["reasoning", "use_just_say_no"],
                            "additionalProperties": False
                        }
                    }
                }
        return json_template

    def call_llm(self, template_name: str, response_format: str, **template_kwargs) -> Dict[str, Any]:
        """Call the LLM with a rendered template."""
        prompt = self._render_template(template_name, **template_kwargs)
        logger.info(f"===PROMPT=== {template_name} \n{prompt}\n===END PROMPT===")
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
            "temperature": 0.0,
            "response_format": self._get_structured_output_format(response_format, **template_kwargs),
            "structured_outputs": True,
            # "thinking": {
            #     "type": "enabled",
            #     "budget_tokens": 500
            # },
            # "max_tokens": 1000
        }
        if self.model_name.startswith("anthropic"):
            payload["thinking"] = {
                "type": "enabled",
                # "budget_tokens": 10000
            }
        max_retries = 3          # total attempts = 1 original + 2 retries
        backoff_base = 1.0       # seconds; grows exponentially

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(self.url, headers=headers, data=json.dumps(payload))
                # If the status isn’t 500, raise_for_status() will do the right thing
                if response.status_code != 500:
                    response.raise_for_status()
                    # print(f"Response status: {response.status_code}")
                    # print(f"Response headers: {response.headers}")
                    # print(f"Response content: {response.text}")
                    return self._extract_json(response)

                # We got a 500 – decide whether to retry.
                print(f"Attempt {attempt}: received 500 from server.")
                if attempt == max_retries:
                    response.raise_for_status()   # will raise HTTPError
            except RequestException as err:
                # Covers network errors as well as HTTPError from raise_for_status()
                # Only retry on the specific 500 case handled above; otherwise bubble up.
                if not getattr(err.response, "status_code", None) == 500:
                    raise

            # Exponential back-off before the next retry
            sleep_time = backoff_base * (2 ** (attempt - 1))
            time.sleep(sleep_time)
        
        raise RuntimeError("call_llm: exhausted retries and still receiving HTTP 500s")



class LLMPlayer(Player, LLMHandler):
    def __init__(self, model_name: str):
        Player.__init__(self, name=model_name)
        LLMHandler.__init__(self, model_name)
        self.model_name = model_name

    @staticmethod
    def convert_to_none(string):
        def contains_alpha(s):
            return any(c.isalpha() for c in s)

        if not string:
            return None
        if type(string) != str:
            return string
        if "null" in string.lower():
            return None
        elif string == "":
            return None
        elif string == "[]":
            return None
        elif not contains_alpha(string):
            return None
        elif string.lower().startswith("string"): # gemini-2.5-pro does this
            return None
        return string
            
    def convert_json_to_action(self, response: dict) -> Optional[Action]:
        action_type_str = self.convert_to_none(response['action_type'])

        try:
            action_type = ActionType[action_type_str]
        except KeyError:
            raise ValueError(f"Invalid action_type '{action_type_str}'")

        card = None
        card_name = self.convert_to_none(response.get('card_name'))
        if action_type != ActionType.PASS:
            if not card_name:
                raise ValueError("'card_name' required for non-PASS actions")
            if action_type == ActionType.MOVE_PROPERTY:
                for pset in self.property_sets.values():
                    if pset.has_card(card_name):
                        card = pset.get_card(card_name)
                        break
                if not card:
                    raise ValueError(f"Card {card_name} not found in properties")
            else:
                card = next((c for c in self.hand if c.name == card_name), None)
            if not card:
                raise ValueError(f"Card {card_name} not found in hand")

        def build_info(data):
            if not data:
                return None
            name = self.convert_to_none(data.get("name"))
            prop_color = self.convert_to_none(data.get("prop_color"))
            if not prop_color or not name:
                return None
            return ActionPropertyInfo(name=name, prop_color=PropertyColor[prop_color])

        double_the_rent_count = self.convert_to_none(response.get('double_the_rent_count'))
        if double_the_rent_count is None:
            double_the_rent_count = 0

        target_property_set = self.convert_to_none(response.get('target_property_set'))
        if target_property_set:
            target_property_set = PropertyColor[target_property_set]
        rent_color = self.convert_to_none(response.get('rent_color'))
        if rent_color:
            rent_color = PropertyColor[rent_color]
        return Action(
            action_type=action_type,
            source_player=self,
            card=card,
            target_player_names=self.convert_to_none(response.get('target_players', [])),
            target_property_set=target_property_set,
            rent_color=rent_color,
            double_the_rent_count=double_the_rent_count,
            forced_deal_source_property_info=build_info(response.get('forced_deal_source_property_info')),
            forced_or_sly_deal_target_property_info=build_info(response.get('forced_or_sly_deal_target_property_info'))
        )
    
    def get_action(self, game_state_dict: dict, game_history: List[str]) -> Optional[Action]:
        """Get the next action from the LLM."""
        response = self.call_llm(
            'get_action_prompt.j2',
            response_format="action",
            player=self,
            game_state=game_state_dict,
            actions_per_turn=ACTIONS_PER_TURN,
            game_history=game_history
        )

        if not isinstance(response, dict):
            raise ValueError(f"LLM response is not json: {response}")
        if 'action_type' not in response:
            raise ValueError("LLM response missing 'action_type'")

        return self.convert_json_to_action(response)

    def choose_cards_to_discard(self, num_cards_to_discard: int, game_state_dict: dict, game_history: List[str]) -> List[Card]:
        """Choose cards to discard using the LLM."""
        response = self.call_llm(
            'choose_cards_to_discard_prompt.j2',
            response_format="discard",
            player=self,
            game_state=game_state_dict,
            num_cards_to_discard=num_cards_to_discard,
            actions_per_turn=ACTIONS_PER_TURN,
            game_history=game_history
        )
        
        discarded_cards = []
        for card_name in response['card_names']:
            card = None
            for c in self.hand:
                if c.name == card_name and c not in discarded_cards:
                    card = c
                    break
            if card:
                discarded_cards.append(card)
                    
        return discarded_cards

    def provide_payment(self, reason: str, amount: int, game_state_dict: dict, game_history: List[str]) -> List:
        """Provide payment using the LLM to choose which cards to use, returning (Card, source) tuples."""
        try:
            response = self.call_llm(
                'provide_payment_prompt.j2',
                response_format="payment",
                player=self,
                reason=reason,
                amount=amount,
                game_state=game_state_dict,
                actions_per_turn=ACTIONS_PER_TURN,
                game_history=game_history
            )
            
            payment_cards = []
            taken = set()
            for item in response['payment']:
                card_name = item['card_name']
                source = item['source']
                card = None
                if source == "bank":
                    for c in self.bank:
                        if c.name == card_name and c not in taken:
                            card = c 
                            taken.add(c)
                            break
                elif source == "properties":
                    # Search all property sets
                    for prop_set in self.property_sets.values():
                        for c in prop_set.cards:
                            if c.name == card_name and c not in taken:
                                card = c
                                taken.add(c)
                                break
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

    def wants_to_negate(self, action_chain_str: str, target_player_name: str, game_state_dict: dict, game_history: List[str]) -> bool:
        """Determine if the player wants to negate an action with a Just Say No card."""
        # Check if we have a Just Say No card
        just_say_no_count = len([c for c in self.hand if c.get_card_type() == CardType.ACTION_JUST_SAY_NO])
        if not just_say_no_count:
            return None
            
        try:
            response = self.call_llm(
                'wants_to_negate_prompt.j2',
                response_format="negate",
                player=self,
                action_chain_str=action_chain_str,
                game_state=game_state_dict,
                actions_per_turn=ACTIONS_PER_TURN,
                game_history=game_history
            )
            
            return response.get('negate', False)
            
        except Exception as e:
            print(f"Error in wants_to_negate: {e}")
            return None

qwen3_235b = LLMPlayer(model_name="qwen/qwen3-235b-a22b:free")
deepseek_r1 = LLMPlayer(model_name="deepseek/deepseek-r1-0528:free")
sarvam_m = LLMPlayer(model_name="sarvamai/sarvam-m:free")
meta_maverick = LLMPlayer(model_name="meta-llama/llama-4-maverick:free")
deepseek_v3_base = LLMPlayer(model_name="deepseek/deepseek-v3-base:free")
gemma3_27b = LLMPlayer(model_name="google/gemma-3-27b-it:free")
gemini_2_5_pro = LLMPlayer(model_name="google/gemini-2.5-pro")
gpt_4_1_nano = LLMPlayer(model_name="openai/gpt-4.1-nano-2025-04-14")
gpt_4_1_mini = LLMPlayer(model_name="openai/gpt-4.1-mini-2025-04-14")
claude_4_sonnet = LLMPlayer(model_name="anthropic/claude-4-sonnet-20250522")
openai_o4_mini = LLMPlayer(model_name="openai/o4-mini")
openai_o3 = LLMPlayer(model_name="openai/o3")

if __name__ == "__main__":

    # handler = LLMHandler(model_name="deepseek/deepseek-r1-0528:free")
    # handler = LLMHandler(model_name="anthropic/claude-4-sonnet-20250522")
    # handler = LLMHandler(model_name="openai/o4-mini")
    # handler = LLMHandler(model_name="openai/o3")
    # handler = LLMHandler(model_name="anthropic/claude-4-sonnet-20250522")
    # handler = LLMHandler(model_name="google/gemini-2.5-pro")
    handler = LLMHandler(model_name="deepseek/deepseek-r1-0528:free")
    handler.call_llm("test_action.j2", response_format="action")
    # handler.call_llm("test_payment.j2", response_format="payment")
    # handler.call_llm("test_discard.j2", response_format="discard", num_cards_to_discard=2)
    # handler.call_llm("test_negate.j2", response_format="negate")