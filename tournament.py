import os
import json
import time
import trio
from typing import List, Dict, Any, Tuple

from game import Game, TestPlayer, setup_logging
from player import Player
from llm import claude_4_sonnet, openai_o4_mini, openai_o3, gemini_2_5_pro

class Tournament:
    """Run a simple 1v1 round robin tournament."""

    def __init__(self, players: List[Player], batch_size: int = 6):
        if len(players) < 2:
            raise ValueError("Tournament requires at least two players.")

        # ensure unique player names
        names = [p.name for p in players]
        if len(names) != len(set(names)):
            raise ValueError("Player names must be unique for a tournament.")

        self.players = players
        self.results: Dict[str, Dict[str, int]] = {
            p.name: {"wins": 0, "losses": 0} for p in players
        }
        self.match_results: List[Dict[str, Any]] = []
        self.tournament_identifier = (
            f"{time.strftime('%Y-%m-%d_%H-%M-%S')}_tournament"
        )
        self.log_dir = os.path.join("logs", self.tournament_identifier)
        os.makedirs(self.log_dir, exist_ok=True)
        self._lock = trio.Lock()
        # ``batch_size`` represents the maximum number of games that will be
        # played concurrently. It defaults to 6 games at once.
        self.batch_size = batch_size

    def _clone_player(self, player: Player) -> Player:
        """Create a fresh instance of a player for a new game."""
        try:
            return player.__class__(getattr(player, "model_name", player.name))
        except Exception:
            return player.__class__(player.name)

    async def _play_match(self, player_a: Player, player_b: Player):
        fresh_players = [self._clone_player(player_a), self._clone_player(player_b)]
        print(f"starting game between {' and '.join([player.name for player in fresh_players])}")
        game = Game(fresh_players)
        await trio.to_thread.run_sync(game.run_game)
        winner = game.game_winner
        if winner is None:
            raise RuntimeError("Game completed without a winner.")
        loser = player_a.name if winner != player_a.name else player_b.name
        async with self._lock:
            self.results[winner]["wins"] += 1
            self.results[loser]["losses"] += 1
            self.match_results.append(
                {
                    "players": [player_a.name, player_b.name],
                    "winner": winner,
                    "game_identifier": game.game_identifier,
                }
            )
            print(f"Game over! Players: {player_a.name}, {player_b.name}.\nWinner: {winner}\nGame Identifier: {game.game_identifier}")

    async def _run_async(self):
        setup_logging(self.tournament_identifier)
        matches: List[Tuple[Player, Player]] = [
            (self.players[i], self.players[j])
            for i in range(len(self.players))
            for j in range(i + 1, len(self.players))
        ]

        # Use workers to ensure that at most ``batch_size`` games are running
        # simultaneously. When one game finishes, a worker immediately begins
        # the next game in the queue.
        send_channel, receive_channel = trio.open_memory_channel[Tuple[Player, Player]](0)

        async def worker():
            async with receive_channel:
                async for a, b in receive_channel:
                    await self._play_match(a, b)

        async with trio.open_nursery() as nursery:
            # start only as many workers as needed
            for _ in range(min(self.batch_size, len(matches))):
                nursery.start_soon(worker)

            async with send_channel:
                for match in matches:
                    await send_channel.send(match)

        self.save_results()

    def run(self):
        trio.run(self._run_async)

    def rankings(self) -> List[Dict[str, Any]]:
        ordered = sorted(
            self.results.items(),
            key=lambda item: (-item[1]["wins"], item[1]["losses"]),
        )
        return [
            {"player": name, "wins": stats["wins"], "losses": stats["losses"]}
            for name, stats in ordered
        ]

    def save_results(self):
        tournament_data = {
            "matches": self.match_results,
            "results": self.results,
            "rankings": self.rankings(),
        }
        with open(os.path.join(self.log_dir, "tournament_results.json"), "w") as f:
            json.dump(tournament_data, f, indent=4)

def run_tournaments(players: List[Player], num_runs: int = 1, batch_size: int = 6):
    """Run multiple tournaments sequentially.

    Args:
        players: List of players participating in each tournament.
        num_runs: Number of tournaments to run.
        batch_size: Number of games to play concurrently within a tournament.
    """

    for i in range(num_runs):
        print(f"Starting tournament {i + 1} of {num_runs}")
        tournament = Tournament(players, batch_size=batch_size)
        tournament.run()


if __name__ == "__main__":
    players = [
        # TestPlayer(name="test_player_1"),
        # TestPlayer(name="test_player_2"),
        # TestPlayer(name="test_player_3"),
        # TestPlayer(name="test_player_4"),
        # TestPlayer(name="test_player_5"),
        # TestPlayer(name="test_player_6"),
        # TestPlayer(name="test_player_7"),
        # TestPlayer(name="test_player_8"),
        # TestPlayer(name="test_player_9"),
        # TestPlayer(name="test_player_10"),
        TestPlayer(name="Randy"),
        openai_o3,
        claude_4_sonnet,
        gemini_2_5_pro,
        openai_o4_mini
    ]

    run_tournaments(players)
