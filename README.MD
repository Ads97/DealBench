# Deal Bench - An AI Research Benchmark inspired by Monopoly Deal\*
LLM Deal Bench is a project that pits different Large Language Models (LLMs) against each other in a simulated game inspired by Monopoly Deal\*. Each player in the arena is controlled either by a random algorithm (for testing) or by an LLM through a specialized player class. Each game progresses over multiple turns, where a player is allowed to make up to 3 actions per turn. A vanilla html/css/javascript frontend displays recent match replays.

## Project Overview 
Backend: Game Simulation (agentdeal/game.py & agentdeal/tournament.py)

An individual game can be run using game.py. The game should support 2-5 players, but has been extensively tested with 2 players. Game mechanics are as follows:

### Game Mechanics

**Game State Representation:** Each player has a hand, a bank for money/action cards and property sets. A central deck manages the remaining cards.

**Action Validation:** A rules engine checks every attempted action by a player - playing cards, banking money, adding/moving properties, playing actions or discarding cards — to ensure it follows game rules.
Win Condition: After each turn the engine verifies whether a player has three complete property sets of different colours to declare the winner. If a player makes 3 invalid actions in a turn, their turn is skipped.

### LLM-Powered Player Control

Player Class: Each player (random bot or LLM) supports 4 types of player moves - get action, provide payment, discard cards, and just say no. For LLM players, each of these moves maps to a prompt in `agentdeal/prompts/`. 

### Tournament Simulation

The tournament is a round-robin tournament that pits each player against every other player. Matches are run in parallel to speed up the tournament. Logs are also stored for each match, as well as aggregate win/loss results.

### Frontend: Visualization (frontend)
1. Data Fetching: The frontend fetches game state and actions played from a simple Flask API.
2. Game Replays: It displays step-by-step replays of the selected game using DOM elements to render each player's cards.

## Running Simulations

**Run a Single Game:** To run a one-off game between two specific models:

`python3 agentdeal/game.py --models openai/o3 anthropic/claude-4-sonnet`
(Use the exact openrouter names for models)

**Deck Configuration:**To change the number/type of cards used, modify the `agentdeal/deck_config.py` file.

**Run Tournaments:** To run a round robin tournament between multiple models:
`python3 agentdeal/tournament.py --models openai/o3 anthropic/claude-4-sonnet`
(Use the exact openrouter names for models)

Use model name `random` to use a random bot (no LLM calls). 

---

## Quick Start
Setup the Environment:

1. Install project dependencies with `pip install -r requirements.txt`.
2. Configure openrouter and openai api keys in a .env file (check out .env.example for the format)
3. Start a Game or Tournament:
    - Use `python3 agentdeal/game.py --models openai/o3 anthropic/claude-4-sonnet` for a single match or `python3 agentdeal/tournament.py --models openai/o3 anthropic/claude-4-sonnet` for a round robin tournament between multiple players. Game logs are written to `logs/`.
4. View Elo rankings: Navigate to `notebooks/elo.ipynb` and run all cells to view elo rankings. 

Launch the Frontend Application:
1. run `python3 frontend_server.py --logs logs/<game-name>`. Do this after running a game or tournament.
2. Open `localhost://5000` in a browser

---

## Architecture Summary
Backend (agentdeal/) (Python): Contains the core game logic (game.py) for simulating a game based on the rules of Monopoly Deal\*. It maintains game state, validates actions, saves logs and can run tournaments to evaluate multiple models.

Frontend (frontend/) (HTML/JS): Provides a lightweight dashboard for viewing game state and replays. It can fetch data from `frontend_server.py` and display it in the browser.

\*This project implements a simulation based on the publicly known rules of Monopoly Deal. Monopoly Deal and Monopoly are registered trademarks of Hasbro, Inc. This project is not affiliated with, endorsed by, or associated with Hasbro in any way.

Made with ❤️ by [Advaith Sridhar](https://advaithsridhar.blog/). Not affiliated with Hasbro. Non commercial use only.

```bibtex
@misc{llm_deal_bench_2025,
  author       = {Advaith Sridhar},
  title        = {Deal Bench: Testing strategy and Improvisation with LLM games},
  year         = {2025},
  howpublished = {\url{https://github.com/advaith/DealBench}},
  note         = {Accessed on: Month Day, Year}
}
```