"""A minimal Flask backend that
1. Serves the static frontend (index.html, index.js, styles.css) from the `frontend/` folder.
2. Exposes `/game_data` that returns example Monopoly Deal game data consumed by `index.js`.

Run with `python server.py` (Python 3.9+) and visit http://localhost:5000
"""
from flask import Flask, jsonify
import json
import os
import glob
import threading
import time
import re

# Tell Flask where the frontend lives and expose it at the root URL ("/")
app = Flask(__name__, static_folder="frontend", static_url_path="")

# Directory containing sequential game state JSON files.
# Can be overridden with the LOG_DIR environment variable.
LOG_DIR = os.environ.get("LOG_DIR", "logs/2025-07-24_06-41-55_openai_o3_google_gemini-2.5-pro_game")

# Shared dictionary that always holds the latest loaded data.
latest_data = {}


def _get_json_files():
    """Return list of game data files sorted by turn then action number."""
    pattern = os.path.join(LOG_DIR, "turn-*_actions-*.json")
    files = glob.glob(pattern)

    def sort_key(path):
        name = os.path.basename(path)
        m = re.match(r"turn-(\d+)_actions-(\d+)\.json", name)
        if m:
            return int(m.group(1)), int(m.group(2))
        return float("inf"), float("inf")

    return sorted(files, key=sort_key)


def update_data_loop():
    """Background loop to load a new file every two seconds."""
    files = _get_json_files()
    idx = 0
    while True:
        if idx < len(files):
            try:
                with open(files[idx], "r") as f:
                    data = json.load(f)
                latest_data.clear()
                latest_data.update(data)
                idx += 1
            except Exception as exc:
                print(f"Failed reading {files[idx]}: {exc}")
        time.sleep(2)


threading.Thread(target=update_data_loop, daemon=True).start()


@app.route("/")
def index():
    """Serve the main HTML page."""
    return app.send_static_file("index.html")


@app.route("/game_data")
def game_data():
    """Return the most recently loaded game data."""
    data = latest_data or {}

    action = ""
    if isinstance(data.get("game_history"), list) and data["game_history"]:
        action = data["game_history"][-1]

    return jsonify({"action": action, "game_state": data.get("game_state", {})})


if __name__ == "__main__":
    # `debug=True` enables hot‑reload so you can iterate quickly during development.
    # Remove it for production or when deploying to environments like Gunicorn.
    app.run(debug=True, port=5000)
