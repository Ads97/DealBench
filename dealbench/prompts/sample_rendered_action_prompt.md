You are an AI player in a game of Agent Deal. Your goal is to win by collecting 3 full property sets of different colors. It is currently your turn. Choose 1 card that you would like to play. Remember, you must play ONLY ONE CARD in this turn.

Here's the set of actions that have occurred so far in the game:

# History

* Play order: openai/o3, Alice

* Dealing initial 5 cards to each player...

* 
--- Starting Game --- 

* 
--- openai/o3's Turn ---

* openai/o3 starts turn.

* openai/o3 has played 0/3 actions.

* openai/o3 added property Wild (Lt.Blue/Brown) to PropertyColor.BROWN

* openai/o3 has played 1/3 actions.


# Game state:
- Current player Turn: openai/o3
- Players: ['openai/o3', 'Alice']
- Turn count: 0
- Actions played in current turn: 1 / 3

Your current game state:
- Hand:


- - name: Debt Collector, value: 3, type: ACTION_DEBT_COLLECTOR

- - name: Crimson Sq, value: 3, type: PROPERTY, set_color: RED, rent_values: [2, 3, 6], num_properties_for_full_set: 3

- - name: $5M, value: 5, type: MONEY

- - name: Property Wildcard (Any Color), value: 0, type: PROPERTY_WILD, available_colors: ['BROWN', 'LIGHT_BLUE', 'PINK', 'ORANGE', 'RED', 'YELLOW', 'GREEN', 'DARK_BLUE', 'RAILROAD', 'UTILITY'], current_color: None

- - name: Forced Deal, value: 3, type: ACTION_FORCED_DEAL

- - name: Rent (Lt.Blue/Brown), value: 1, type: ACTION_RENT, colors: ['LIGHT_BLUE', 'BROWN']


- Bank (Total value: 0):

  None.

- Property Sets:

  
  - BROWN:
    Cards:
    
    
      - name: Wild (Lt.Blue/Brown), value: 1, type: PROPERTY_WILD, available_colors: ['LIGHT_BLUE', 'BROWN'], current_color: BROWN
    
    
    Full Set: False
    House: False, Hotel: False
    Rent: 
  


Other players:

  

  
- Alice:
  - Bank (Total value: 0):
    
    None.
    
  - Property Sets:
    
      None.
    
  



Available actions:
1. Play a property card from your hand
2. Move a wild property card from one property set to another (does not consume an action). If a wild property card is used to start a property set, you must specify the set color (can be only 1 color).
3. Play a money card to your bank
4. Play an action card (e.g. Rent, Pass Go, Birthday, Debt Collector, Sly Deal, Forced Deal, Deal Breaker, Just Say No, etc.)
5. End your turn

---

# Action JSON Structure
Your response **must** be a single JSON object describing the action you will take. Only include fields relevant to your chosen action type. See the table below for all possible fields:

| Field Name                        | Required? | Description                                                                                       | Example Value                                  |
|-----------------------------------|-----------|---------------------------------------------------------------------------------------------------|------------------------------------------------|
| reasoning                         | Always    | Short explanation for why you chose this action                                                   | "Playing rent to maximize income"              |
| action_type                       | Always    | One of: ADD_TO_PROPERTIES, MOVE_PROPERTY, ADD_TO_BANK, PLAY_ACTION, PASS                         | "PLAY_ACTION"                                 |
| card_name                         | If using a card | The name of the card from your hand (or properties for MOVE_PROPERTY)                         | "Blue Property", "Deal Breaker"               |
| target_players                    | If action targets players | List of player names to target (e.g. for Rent, Sly Deal, Forced Deal, etc.)            | ["Alice"]                                     |
| target_property_set               | If action targets a property set | The color name of the property set to target (or move to) | "RED", "BLUE"                                  |
| rent_color                        | If playing a Rent card | The color to charge rent for (must be a valid color for the Rent card and in your property sets)                 | "GREEN"                                       |
| double_the_rent_count             | If using Double the Rent | Number of Double the Rent cards to play with a Rent card (each consumes an action)     | 1, 2                                            |
| forced_deal_source_property_info  | Forced Deal only | Object: {"name": card_name, "prop_color": color_name} for your property to trade        | {"name": "Orange Property", "prop_color": "ORANGE"} |
| forced_or_sly_deal_target_property_info | Forced/Sly Deal only | Object: {"name": card_name, "prop_color": color_name} for target property | {"name": "Red Property", "prop_color": "RED"}      |

---

# Detailed Examples

## 1. Play a property card from your hand
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "ADD_TO_PROPERTIES",
  "card_name": "Property Name",
  "target_players": null,
  "target_property_set": "BLUE",
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": null
}

## 2. Move a wild property card between sets
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "MOVE_PROPERTY",
  "card_name": "Wild Property",
  "target_players": null,
  "target_property_set": "GREEN",
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": null
}

## 3. Play a money card to your bank
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "ADD_TO_BANK",
  "card_name": "$5M",
  "target_players": null,
  "target_property_set": null,
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": null
}

## 4. Play an action card
### a. Rent Card (with Double the Rent)
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "PLAY_ACTION",
  "card_name": "Rent (Pink/Orange)",
  "target_players": ['Alice', 'Bob'],
  "target_property_set": null,
  "rent_color": "PINK", // you must have a PINK card in your properties (not hand)
  "double_the_rent_count": 1,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": null
}

### b. Sly Deal
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "PLAY_ACTION",
  "card_name": "Sly Deal",
  "target_players": ['Alice'],
  "target_property_set": null,
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": {
    "name": "Wild (Pink/Orange)",
    "prop_color": "PINK"
  }
}

### c. Forced Deal
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "PLAY_ACTION",
  "card_name": "Forced Deal",
  "target_players": ['Alice'],
  "target_property_set": null,
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": {
    "name": "Orange Property",
    "prop_color": "ORANGE"
  },
  "forced_or_sly_deal_target_property_info": {
    "name": "Property Name",
    "prop_color": "RED"
  }
}

### d. Deal Breaker
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "PLAY_ACTION",
  "card_name": "Deal Breaker",
  "target_players": ['Alice'],
  "target_property_set": "BLUE",
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": null
}

### e. Pass Go, It's My Birthday, Debt Collector
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "PLAY_ACTION",
  "card_name": "Pass Go",
  "target_players": null,
  "target_property_set": null,
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": null
}
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "PLAY_ACTION",
  "card_name": "It's My Birthday",
  "target_players": ['Alice', 'Bob'],
  "target_property_set": null,
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": null
}
{
  "reasoning": "One line reasoning on what action you should choose",
  "action_type": "PLAY_ACTION",
  "card_name": "Debt Collector",
  "target_players": ['Alice'],
  "target_property_set": null,
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": null
}

## 5. End your turn
{
  "reasoning": "No strong plays left this turn",
  "action_type": "PASS",
  "card_name": null,
  "target_players": null,
  "target_property_set": null,
  "rent_color": null,
  "double_the_rent_count": null,
  "forced_deal_source_property_info": null,
  "forced_or_sly_deal_target_property_info": null
}

---

# Guidance
- Only include fields relevant to the action you are taking. Fill the rest with 'null'.
- Always use the exact card name as it appears in your hand or properties.
- For Rent, specify rent_color and double_the_rent_count if using Double the Rent cards.
- For actions targeting other players or property sets, always specify the correct player names and property set colors.
- If you are unsure, refer to the above examples.

Choose the one best card to play based on the current game state. Your response must be a single JSON object in the above format.
