Monopoly Deal requirements:
1. Allow 1 game with multiple rounds (until any player wins), 2-5 players. 
2. Each player has hidden set of cards and public deck of cards 
3. Central shuffled deck of cards. What happens when cards run out

3 types of cards:
1. Action Cards. 
1a. rent cards. have 2 colours on them. Choose one of the colours shown on the card and collect rent based on what the card says. Rent can only be collected on properties you own (not on other players properties). 
1b. double the rent cards. can be paired with any rent card. must be played at the same time as a rent cad, and it counts as one of the three cards you may play on your turn. Collect double rent!
1c. house and hotel cards. add to a complete property set. cannot be placed on railroads and utilities. discarded if the property set they are on becomes incomplete. hotel can only be placed if there's already a house on it. (you collect rent for hotel and house separately.). A property set may have only one of each. 
1d. Just say no cards. can be used even when its not your turn. cancels action cards played against you. Impacts only you, not any other player. If another player uses a just say no card too, then yours is cancelled. If played during your turn, counts towards on your three actions. 
2. Property Cards - these occur in sets. railroads and utilities are separate from location properties. Collect three complete sets, each in a different colour, to win. You can never place them in your bank. The value of the card is used to pay another player. Rent you collect when you play a rent action card is denoted on it, based on how many properties you own in the set. The number of properties in the colour set is also denoted on the card. 
2b. wild property cards - you can choose the colour they represent. They can be used to complete property sets. Once placed, you can always change which colour you'd like them to represent later in the game as long as you do so during your turn. Changing the colour does not count as playing a new card. They cannot be placed in the bank. 4 colour wild card cannot be used as money. 
3. Money cards: put these in your bank and use them to pay other players. If you run out of money and need to pay another player, you must use your properties if they are present. 

Rules:
How to win: Be the first player to collect 3 complete property sets. Each set must be a different colour. For example: you can't win with 2 red sets and 1 blue set. 

Who goes first: The play order is randomly decided at the beginning of the game. 

On your turn: 
1. Draw two cards: If you ever start your turn with no cards, draw 5 instead. 
2. Play up to 3 cards of any type. You may choose to play none. 
- Playing Cards: There are three ways to play cards. You don't have to do all of these in one turn (remember, you don't even have to play any cards at all). Once you play a card, you can't put it back in your hand. See the cards section to know about them. 
- Add to your bank by placing money or action cards with the add_to_bank function. Action cards are worth the amount shown on the top left of the card. Once you place an action card in your bank, think of it as a money card - you can't do the action on it once it's in there. You'll need money in your bank to pay other players. 
- Add a property to your collection by placing it faceup in front of you, separate from your Bank. You may place as many properties as you want throughout the game, but rememver you need 3 complete sets of different colours to win. 
- Play an action card by calling the play_action_card function. The action card gets discared when done - except house and hotel cards, which get added to your property sets. 
3. At the end of your turn, you may have up to 7 cards in your hand. If you have more than 7, choose which extras to place in the discard pile. (it's okay to end your turn with no cards!)

Paying other players: Owe another player money? You can pay in two ways:
1. Pay from your Bank. Give the player money or action cards from your Bank, which go to the other player's Bank. 
2. Pay with your properties. Properties are worth the amount shown on the left of the card and go to the other player's property collection. Properties never go in the Bank!

You choose how you want to pay, not the player you're paying. Never pay with cards from your hand. if you don't have enough in your Bank, then you must pay with your properties!

There's no change in this game, so you may have to pay more than what you owe if that's all you have. For example: if you owe $2Million, have a $5Million if your Bank and no properties, then you must give them $5Million. 
If you don't have enough money or properties, just pay what you can. If you have no money or properties, nothing happens. 
You can't pay with cards from your hand.



How the system will work

1. All cards in a config 
2. At each turn, LLM will get a prompt with the entire rule set, current state of the board for all players, number of cards in each player's hand, and tools they can call. History of turns is optional, not in for now 
Game should be playable by humans as well with same list of APIs through a UI. 




Design principles:
1. Don't provide set of legal moves to the LLM. Ability to figure out legal moves is part of the test. 



Classes to have:
1. Player - Exposes a get_action function that returns an action. ABC with subclasses HumanPlayer and LLMPlayer. get_action can return Action object or None 
2. Game Engine - initialize game state, decide player order and current player, check legal action, implements action on game state, requests other players to respond to action if needed, check for win condition. Stateless. 
3. GameState - contains state of the game at any point, purely data 
4. Card - class that contains all card properties 
5. Action - action type (add_to_bank, play_action_card, add_to_properties, discard), which card, source player, target player
6. Rules - given game state, source player, action, decides if it is a valid move. 
7. 


Sources:
https://www.buffalolib.org/sites/default/files/gaming-unplugged/inst/Monopoly%20Deal%20Card%20Game%20Instructions.pdf
