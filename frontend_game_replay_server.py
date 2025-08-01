"""A minimal Flask backend that
1. Serves the static frontend (index.html, index.js, styles.css) from the `frontend/` folder.
2. Exposes `/game_data` that returns example Monopoly Deal game data consumed by `index.js`.

Run with `python frontend_game_replay_server.py` (Python 3.9+) and visit http://localhost:5000
"""
from flask import Flask, jsonify
import json
import os
import glob
import re
from threading import Lock

# Tell Flask where the frontend lives and expose it at the root URL ("/")
app = Flask(__name__, static_folder="frontend/simple", static_url_path="")

# Directory containing sequential game state JSON files.
# Can be overridden with the LOG_DIR environment variable.
LOG_DIR = os.environ.get("LOG_DIR", "logs/2025-08-01_07-45-03_google_gemini-2.5-pro_openai_o3_game")

# Shared dictionary that always holds the latest loaded data.
latest_data = {}


def _get_json_files():
    """Return list of game data files sorted by turn then action number.

    The list includes all ``turn-*_actions-*.json`` files followed by the
    ``result.json`` file (if present) so that the frontend receives the final
    game summary after all turn data has been served.
    """
    pattern = os.path.join(LOG_DIR, "turn-*_actions-*.json")
    files = glob.glob(pattern)

    def sort_key(path):
        name = os.path.basename(path)
        m = re.match(r"turn-(\d+)_actions-(\d+)\.json", name)
        if m:
            return int(m.group(1)), int(m.group(2))
        return float("inf"), float("inf")

    files = sorted(files, key=sort_key)

    # Append the result.json file at the end if it exists.
    result_path = os.path.join(LOG_DIR, "result.json")
    if os.path.exists(result_path):
        files.append(result_path)

    return files


files = []
idx = 0
idx_lock = Lock()


def load_next_data():
    """Load the next log file on demand."""
    global files, idx
    if not files:
        files = _get_json_files()
    if idx < len(files):
        try:
            with open(files[idx], "r") as f:
                data = json.load(f)
            latest_data.clear()
            latest_data.update(data)
            idx += 1
        except Exception as exc:
            print(f"Failed reading {files[idx]}: {exc}")


@app.route("/")
def index():
    """Serve the main HTML page."""
    return app.send_static_file("simple.html")


@app.route("/game_data")
def game_data():
    """Return the most recently loaded game data."""
    with idx_lock:
        load_next_data()
    data = latest_data or {}

    action = ""
    if isinstance(data.get("game_history"), list) and data["game_history"]:
        action = data["game_history"][-1]

    metadata = data.get("metadata")
    if metadata:
        reasoning = metadata.get("reasoning", "")
    else:
        reasoning = ""

    return jsonify({
        "action": action,
        "game_state": data.get("game_state", {}),
        "winner": data.get("winner"),
        "reasoning": reasoning
    })


if __name__ == "__main__":
    # `debug=True` enables hot‑reload so you can iterate quickly during development.
    # Remove it for production or when deploying to environments like Gunicorn.
    app.run(debug=True, port=5000)
