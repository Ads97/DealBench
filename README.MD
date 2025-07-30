# LLM Deal Arena
LLM Deal Arena is a project that pits different Large Language Models (LLMs) against each other in a competitive Monopoly Deal game simulation. Each player in the arena is controlled either by a random algorithm (for testing) or by an LLM through a specialized player class. Each game progresses over multiple turns, where a player is allowed to make up to 3 actions per turn. The complete set of rules can be found [here](https://monopolydealrules.com/). The game is played with all the action, money and property cards. A vanilla html/css/javascript frontend displays recent match replays.

## Project Overview
Backend: Game Simulation (backend/main.py & backend/run_batch.py)
Game Mechanics:

Snake Representation: Each snake is represented as a deque of board positions. The game handles moving the snake's head, updating the tail, and managing growth when an apple is eaten.
Collision Logic: The game checks for collisions—with walls, with snake bodies (including self-collisions), and with head-to-head moves [if two or more snake heads land on the same cell].
Rounds and Game-Over: The simulation proceeds round-by-round. Rounds end when one snake remains or when a maximum round count is reached. The game then records the outcome (score, win/loss/tie, history) and saves the complete game state as a JSON file.
LLM-Powered Snake Control:

LLMPlayer Class: For each snake, if controlled by an LLM, the game constructs a detailed prompt of the board state (including positions of all snakes and apples) and the last move's rationale. This prompt is sent to an LLM provider, which returns a recommendation for the next direction.
Fallback Mechanism: If the response from the LLM is unclear, the snake falls back to selecting a random valid move.
Batch Simulation (run_batch.py):

Orchestrates running a target LLM against multiple opponent LLMs.
Supports filtering opponents based on cost criteria defined in backend/model_lists/model_list.yaml.
Uses Python's concurrent.futures for efficient, in-process parallel execution of simulations.
Allows configuration of the number of simulations per matchup and the degree of parallelism.
Frontend: Visualization & Dashboard (frontend/src/app/page.tsx)
Leaderboard & Latest Matches:

Data Fetching: The frontend fetches aggregated statistics (e.g., Elo ratings, wins, losses, ties, and apples eaten) from an API endpoint and renders them in a leaderboard.
Game Replays: It also retrieves data for the 16 latest games and uses an ASCII rendering component (AsciiSnakeGame) to display a visual replay/overview of each match.
User Interface:

An animated title and additional descriptive texts offer context to the users—explaining what happens when two LLM-driven snakes battle, along with providing real-time updates on match outcomes.
Running Simulations
Run a Single Game: To run a one-off game between two specific models:

cd backend
# Replace model names with valid IDs from model_list.yaml
python3 main.py --models gpt-4o-mini-2024-07-18 claude-3-haiku-20240307 
To use Ollama models (assuming they are configured in model_list.yaml with the ollama- prefix in their name), use the prefixed name:

cd backend
python3 main.py --models ollama-llama3.2 ollama-llama3.3 
You can also customize game parameters like --width, --height, --max_rounds, and --num_apples.

Run Batch Simulations (Target Model vs. Others): To test a specific model against a pool of opponents, use the run_batch.py script.

cd backend

# Basic usage: Run 'my-new-model' against all valid opponents 5 times each
python3 run_batch.py --target-model "my-new-model" --num-simulations 5

# With cost filtering: Only run against opponents cheaper than $1.00/million output tokens
python3 run_batch.py --target-model gpt-4.1-2025-04-14 --num-simulations 5 --max-output-cost-per-million 10.0

# Control parallelism: Limit to 8 concurrent simulations
python3 run_batch.py --target-model "my-new-model" --num-simulations 5 --max-workers 8

# Full example: Cost filtering and parallelism control
python3 run_batch.py --target-model "my-new-model" --num-simulations 5 --max-output-cost-per-million 1.0 --max-workers 8
This script uses the pricing information in backend/model_lists/model_list.yaml for filtering. Models without valid pricing information will be skipped during filtering. Game parameters (--width, etc.) can also be passed to run_batch.py.

Run Elo Tracker: After running simulations, update the Elo ratings based on the completed games:

cd backend
python3 elo_tracker.py completed_games --output completed_games
Quick Start
Setup the Environment:

Install project dependencies (pip install -r requirements.txt in backend).
Ensure that your environment variables (e.g., API keys for your LLM provider) are configured via a .env file in the backend directory.
Update backend/model_lists/model_list.yaml with the models you want to test and their pricing information.
Start Backend Simulations:

Use the python3 main.py command for single games or python3 run_batch.py for testing a model against multiple opponents. Simulations generate JSON files in backend/completed_games/.
Launch the Frontend Application:

Navigate to the frontend directory.
Install dependencies (npm install or yarn install).
Start the Next.js development server to see the leaderboard and replays.
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
Architecture Summary
Backend (Python): Contains the core game logic (main.py) for simulating a snake game where each snake can be controlled by an LLM. It tracks game state, records round-by-round history, manages collisions and apple spawning, and decides game outcomes. A separate script (run_batch.py) handles running a target model against multiple opponents in parallel, with options for cost-based filtering.

Frontend (Next.js): Provides a visual dashboard for game results. It pulls data via APIs to render leaderboards and ASCII-based match replays clearly showing the state of the board.

Made with ❤️ by Greg Kamradt

@misc{snake_bench_2025,
  author       = {Greg Kamradt},
  organization = {ARC Prize Foundation},
  title        = {Snake Bench: Competitive Snake Game Simulation with LLMs},
  year         = {2025},
  howpublished = {\url{https://github.com/gkamradt/SnakeBench}},
  note         = {Accessed on: Month Day, Year}
}