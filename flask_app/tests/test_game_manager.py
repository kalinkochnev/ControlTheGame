import unittest
from unittest.mock import patch

from flask_app.TrackingThread import GameObject, GameManager, Tracker, CurrentState, Settings


class GameManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = GameManager()

    def test_add_to_blocked(self):
        game = GameObject.min_init("game1", 100)
        self.manager.blocked_games = [game]

        self.manager.block(game)
        self.assertEqual([game], self.manager.blocked_games)

        self.manager.blocked_games = []
        self.manager.block(game)
        self.assertEqual([game], self.manager.blocked_games)

    def test_blocked_game_names(self):
        game_names = ["A", "B", "C"]
        self.manager.blocked_games = [GameObject.min_init(name, 100) for name in game_names]
        self.assertEqual(game_names, self.manager.blocked_names())

    def test_update_block(self):
        with patch("flask_app.TrackingThread.GameObject.has_time") as mock_time:
            mock_time.return_value = True
            game_obj = GameObject.min_init("game1", 1)
            game_obj2 = GameObject.min_init("game2", 1)

            settings = Settings(0, 1, [game_obj, game_obj2])
            current_state = CurrentState(settings)
            current_state.currently_running = [game_obj, game_obj2]

            self.manager.update_block(current_state)
            self.assertEqual([], self.manager.blocked_games)

            mock_time.return_value = False
            self.manager.update_block(current_state)
            self.assertEqual([game_obj, game_obj2], self.manager.blocked_games)

    def test_enforce_block(self):
        with patch("flask_app.TrackingThread.GameObject.kill") as mock_kill:
            game_obj = GameObject.min_init("game1", 1)
            game_obj2 = GameObject.min_init("game2", 1)

            settings = Settings(0, 1, [game_obj, game_obj2])
            current_state = CurrentState(settings)
            current_state.currently_running = [game_obj, game_obj2]

            self.manager.blocked_games = [game_obj]
            self.manager.enforce_block(current_state)

            self.assertEqual([game_obj2], current_state.currently_running)


if __name__ == '__main__':
    unittest.main()
