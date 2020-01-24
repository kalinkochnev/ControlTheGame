import unittest

from flask_app.TrackingThread import Settings, GameObject


class SettingsTests(unittest.TestCase):
    def test_creation(self):
        game_obj = GameObject.min_init("game1", 1)
        game_obj2 = GameObject.min_init("game2", 1)
        settings = Settings(0, 1, [game_obj, game_obj2])
        self.assertEqual(game_obj, settings.tracking_games[0])
        self.assertEqual(game_obj2, settings.tracking_games[1])
        settings.extra_time = 0
        settings.loop_time = 1


if __name__ == '__main__':
    unittest.main()
