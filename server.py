"""A minimal Flask backend that
1. Serves the static frontend (index.html, index.js, styles.css) from the `frontend/` folder.
2. Exposes `/game_data` that returns example Monopoly Deal game data consumed by `index.js`.

Run with `python server.py` (Python 3.9+) and visit http://localhost:5000
"""
from flask import Flask, jsonify
import json
import os 

# Tell Flask where the frontend lives and expose it at the root URL ("/")
app = Flask(__name__, static_folder="frontend", static_url_path="")


@app.route("/")
def index():
    """Serve the main HTML page."""
    return app.send_static_file("index.html")


@app.route("/game_data")
def game_data():
    """Return a very small, hard‑coded snapshot of game state for demo purposes.
    Replace or extend this with your real game engine / database call.
    """
    print(os.getcwd())
    result = "logs/2025-07-09_20-46-24_anthropic_claude-4-sonnet-20250522_openai_o3_game/result.json"
    with open(result, "r") as f:
        data = json.load(f)
    
    return jsonify(data['game_state'])


if __name__ == "__main__":
    # `debug=True` enables hot‑reload so you can iterate quickly during development.
    # Remove it for production or when deploying to environments like Gunicorn.
    app.run(debug=True, port=5000)
