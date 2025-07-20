"""A minimal Flask backend that
1. Serves the static frontend (index.html, index.js, styles.css) from the `frontend/` folder.
2. Exposes `/game_data` that returns example Monopoly Deal game data consumed by `index.js`.

Run with `python server.py` (Python 3.9+) and visit http://localhost:5000
"""
from flask import Flask, jsonify

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
    sample_data = {
        "players": [
            {
                "name": "Alice",
                "hand_cards": [
                    {"name": "Deal Breaker", "value": 5, "type": "ACTION"},
                    {"name": "Just Say No", "value": 4, "type": "ACTION"},
                ],
                "banked_cards": [
                    {"name": "5M", "value": 5, "type": "MONEY"},
                    {"name": "2M", "value": 2, "type": "MONEY"},
                ],
                "property_sets": {
                    "BLUE": {
                        "cards": [
                            {"name": "Boardwalk", "value": 4, "type": "PROPERTY"},
                            {"name": "Park Place", "value": 4, "type": "PROPERTY"},
                        ]
                    },
                    "RED": {
                        "cards": [
                            {"name": "Kentucky Avenue", "value": 3, "type": "PROPERTY"}
                        ]
                    },
                },
            },
            {
                "name": "Bob",
                "hand_cards": [
                    {"name": "Pass Go", "value": 1, "type": "ACTION"},
                ],
                "banked_cards": [
                    {"name": "10M", "value": 10, "type": "MONEY"},
                ],
                "property_sets": {
                    "GREEN": {
                        "cards": [
                            {"name": "Pacific Avenue", "value": 4, "type": "PROPERTY"},
                            {
                                "name": "North Carolina Avenue",
                                "value": 4,
                                "type": "PROPERTY",
                            },
                        ]
                    }
                },
            },
        ]
    }
    return jsonify(sample_data)


if __name__ == "__main__":
    # `debug=True` enables hot‑reload so you can iterate quickly during development.
    # Remove it for production or when deploying to environments like Gunicorn.
    app.run(debug=True, port=5000)
