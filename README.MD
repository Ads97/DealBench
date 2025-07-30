# LLM Deal Arena
LLM Deal Arena is a project that pits different Large Language Models (LLMs) against each other in a competitive Monopoly Deal game simulation. Each player in the arena is controlled either by a random algorithm (for testing) or by an LLM through a specialized player class. Each game progresses over multiple turns, where a player is allowed to make up to 3 actions per turn. The complete set of rules can be found [here](https://monopolydealrules.com/). The game is played with all the action, money and property cards. A vanilla html/css/javascript frontend displays recent match replays.

## Project Overview
Backend: Game Simulation (game.py & tournament.py)
Game Mechanics:

Game State Representation: Each player has a hand, a bank for money/action cards, property sets and a personal discard pile. A central deck manages the remaining and discarded cards.
Action Validation: A rules engine checks every attempted move—playing a card, banking money, adding properties, moving cards or paying debts—to ensure it follows Monopoly Deal rules.
Win Condition: After each turn the engine verifies whether a player has three complete property sets of different colours to declare the winner.
LLM-Powered Player Control:

LLMPlayer Class: For each player controlled by an LLM, the engine constructs a detailed prompt describing the game state (hands, banks, properties, deck counts) and the previous turn's reasoning. The LLM returns a recommended action to execute.
Fallback Mechanism: If the response from the LLM is unclear, the player falls back to selecting a random valid move.
Tournament Simulation (tournament.py):

Runs multiple matchups in parallel to evaluate LLM strategies.
Stores logs for each match and aggregates win/loss results.
Frontend: Visualization (frontend)
Leaderboard & Latest Matches:

Data Fetching: The frontend can fetch aggregated statistics such as Elo ratings and recent results from a simple Flask API.
Game Replays: It displays step-by-step replays of the latest games using DOM elements to render each player's cards.
User Interface:

A basic HTML/JS interface shows the board state and pops up the winner when a game finishes.
Running Simulations
Run a Single Game: To run a one-off game between two specific models:

python3 game.py --models gpt-4o-mini-2024-07-18 claude-3-haiku-20240307
You can also customize game parameters like number of players or the deck configuration.

Run Tournaments (Target Model vs. Others): To test a specific model against a pool of opponents, use tournament.py.

python3 tournament.py
This script spins up multiple games concurrently and saves the logs in the logs/ directory.

Quick Start
Setup the Environment:

Install project dependencies with `pip install -r requirements.txt`.
Ensure that your environment variables (e.g., API keys for your LLM provider) are configured in a .env file.
Start a Game or Tournament:

Use `python3 game.py` for a single match or `python3 tournament.py` for repeated matches between multiple players. Game logs are written to `logs/`.
Launch the Frontend Application:

Navigate to the `frontend` directory.
Open `index.html` in a browser or run `python3 frontend_server.py` to serve replays via Flask.

Architecture Summary
Backend (Python): Contains the core game logic (game.py) for simulating Monopoly Deal. It maintains game state, validates actions, saves logs and can run tournaments to evaluate multiple models.

Frontend (HTML/JS): Provides a lightweight dashboard for viewing game state and replays. It can fetch data from `frontend_server.py` and display it in the browser.

Made with ❤️ by Greg Kamradt

@misc{llm_deal_arena_2025,
  author       = {Greg Kamradt},
  title        = {LLM Deal Arena: Competitive Monopoly Deal with LLMs},
  year         = {2025},
  howpublished = {\url{https://github.com/gkamradt/AgentDeal}},
  note         = {Accessed on: Month Day, Year}
}
