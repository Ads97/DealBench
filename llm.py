import os
import json
import requests
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from player import Player
from action import Action, ActionType
from card import Card
from deck_config import ACTIONS_PER_TURN
load_dotenv()

class LLMHandler():
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.template_env = Environment(loader=FileSystemLoader('prompts'))

    def _render_template(self, template_name: str, **kwargs) -> str:
        """Render a Jinja2 template with the given context."""
        template = self.template_env.get_template(template_name)
        return template.render(**kwargs)

    def call_llm(self, template_name: str, **template_kwargs) -> Dict[str, Any]:
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
            # "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response content: {response.text}")
            result = response.json()
            return json.loads(result['choices'][0]['message']['content'])
        except Exception as e:
            print(f"Error calling LLM: {e}")
            raise


class LLMPlayer(Player, LLMHandler):
    def __init__(self, model_name: str):
        Player.__init__(self, name=model_name)
        LLMHandler.__init__(self, model_name)
        self.model_name = model_name

    def get_action(self, game_state_dict: dict) -> Optional[Action]:
        """Get the next action from the LLM."""
        try:
            response = self.call_llm(
                'get_action_prompt.j2',
                player=self,
                game_state=game_state_dict,
                actions_per_turn=ACTIONS_PER_TURN
            )
            
            if response.get('action_type') == 'PASS':
                return None
                
            # Find the card in hand by name
            card = next((c for c in self.hand if c.name == response.get('card_name')), None)
            if not card and response.get('action_type') != 'PASS':
                print(f"Card {response.get('card_name')} not found in hand")
                return None
                
            return Action(
                action_type=ActionType[response['action_type']],
                source_player=self,
                card=card,
                target_player_names=response.get('target_players', []),
                target_property_set=response.get('target_property_set'),
                rent_color=response.get('rent_color'),
                double_the_rent_count=response.get('double_the_rent_count', 0)
            )
            
        except Exception as e:
            print(f"Error in get_action: {e}")
            return None

    def choose_cards_to_discard(self, num_cards_to_discard: int, game_state_dict: dict) -> List[Card]:
        """Choose cards to discard using the LLM."""
        try:
            response = self.call_llm(
                'choose_cards_to_discard_prompt.j2',
                player=self,
                game_state=game_state_dict,
                num_cards_to_discard=num_cards_to_discard
            )
            
            # Convert card names to Card objects
            discarded_cards = []
            for card_name in response:
                card = next((c for c in self.hand if c.name == card_name), None)
                if card:
                    discarded_cards.append(card)
                        
            return discarded_cards
            
        except Exception as e:
            print(f"Error in choose_cards_to_discard: {e}")
            return None

    def provide_payment(self, reason: str, amount: int) -> List:
        """Provide payment using the LLM to choose which cards to use, returning (Card, source) tuples."""
        try:
            response = self.call_llm(
                'provide_payment_prompt.j2',
                player=self,
                reason=reason,
                amount=amount
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

    def wants_to_negate(self, action: Action) -> bool:
        """Determine if the player wants to negate an action with a Just Say No card."""
        # Check if we have a Just Say No card
        just_say_no = next((c for c in self.hand if c.name == 'Just Say No'), None)
        if not just_say_no:
            return False
            
        try:
            response = self.call_llm(
                'wants_to_negate_prompt.j2',
                player=self,
                action=str(action)
            )
            
            return response.get('negate', False)
            
        except Exception as e:
            print(f"Error in wants_to_negate: {e}")
            return False

qwen3_235b = LLMPlayer(model_name="qwen/qwen3-235b-a22b:free")
deepseek_r1_0528 = LLMPlayer(model_name="deepseek/deepseek-r1-0528:free")
sarvam_m = LLMPlayer(model_name="sarvamai/sarvam-m:free")
meta_maverick = LLMPlayer(model_name="meta-llama/llama-4-maverick:free")
deepseek_v3_base = LLMPlayer(model_name="deepseek/deepseek-v3-base:free")
gemma3_27b = LLMPlayer(model_name="google/gemma-3-27b-it:free")
gemini_2_5_pro_experimental = LLMPlayer(model_name="google/gemini-2.5-pro-exp-03-25") #think its free?