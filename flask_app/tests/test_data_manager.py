import time
import unittest
import os
from unittest.mock import patch

from flask_app.TrackingThread import GameObject, DataManager, Settings


class TestDataManager(unittest.TestCase):
    def setUp(self) -> None:
        self.base_loc = Settings.get_base_loc("ControlTheGame")
        self.db_loc = ""
        self.init_test_db()

        self.game_obj1 = GameObject.min_init("game1", 0)
        self.game_obj2 = GameObject.min_init("game2", 0)
        self.settings = Settings(5, 1, [self.game_obj1, self.game_obj2])
        self.settings.db_loc = self.db_loc
        self.data_m = DataManager()
        self.db = self.data_m.get_db()

    def tearDown(self) -> None:
        self.init_test_db()

    # WARNING if sql execution script is moved, that's a big issue!
    def init_test_db(self):
        self.db_loc = os.path.join(self.base_loc, "flask_app/tests/test_resources/test_db.sqlite")
        sql_script_loc = os.path.join(self.base_loc, "flask_app/flaskr/schema.sql")

        if os.path.isfile(self.db_loc) is False:
            db_file = open(self.db_loc, "w+")
            db_file.close()

        with open(sql_script_loc, "r") as script:
            db = DataManager.get_db()
            db.executescript(script.read().strip())

    def test_db_creation(self):
        self.assertTrue(os.path.exists(self.db_loc))

    def test_store_game_obj(self):
        conn = self.db.cursor()
        game_obj = GameObject("test game", time.time(), time.time() + 1000, 2000)
        self.data_m.store_new(game_obj)
        result = self.data_m.query("SELECT * FROM game_log WHERE name='test game' LIMIT 1;", single=True)

        self.assertEqual(game_obj.name, result['name'])
        self.assertEqual(int(game_obj.start_time), result['start_time'])
        self.assertEqual(int(game_obj.end_time), result['end_time'])
        self.assertEqual(int(game_obj.max_time), result['max_time'])

    def test_to_obj(self):
        game_obj = GameObject("test game", time.time(), time.time() + 1000, 2000)
        self.data_m.store_new(game_obj)
        result = self.data_m.query("SELECT * FROM game_log WHERE name='test game' LIMIT 1;", single=True)
        to_obj = self.data_m.to_obj(result)
        self.assertTrue(game_obj.deep_equal(to_obj))

    def test_get(self):
        game_obj = GameObject("game", 0, 100, 10)
        self.data_m.store_new(game_obj)

        with patch("flask_app.TrackingThread.DataManager.query") as patched:
            query = "SELECT * FROM game_log WHERE max_time=10 AND name='game' LIMIT 1;"
            self.data_m.get(max_time=10, name="game")
            patched.assert_called_with(query, single=True)

            query = "SELECT * FROM game_log WHERE max_time=10 AND name='game' AND end_time=100 AND start_time=0 LIMIT 1;"
            self.data_m.get(max_time=10, name="game", end_time=100, start_time=0)
            patched.assert_called_with(query, single=True)

        self.assertIsNone(self.data_m.get())
        self.assertTrue(game_obj.deep_equal(self.data_m.get(name="game")))

    def test_store_many(self):
        game1 = GameObject("game1", time.time(), time.time() + 100, 200)
        game2 = GameObject("game2", time.time() - 50, time.time() + 100, 200)

        self.data_m.store_many(game1, game2)
        game_obj = self.data_m.get(name="game1")
        game_obj2 = self.data_m.get(name="game2")
        self.assertTrue(game1.deep_equal(game_obj))
        self.assertTrue(game2.deep_equal(game_obj2))

    def test_get_many(self):
        game1 = GameObject("game1", time.time(), time.time() + 100, 200)
        game2 = GameObject("game2", time.time() - 50, time.time() + 100, 200)
        self.data_m.store_many(game1, game2)

        objs = self.data_m.get_many()

        self.assertTrue(game1.deep_equal(objs[0]))
        self.assertTrue(game2.deep_equal(objs[1]))

        objs = self.data_m.get_many(limit="yay")
        self.assertEqual([], objs)

        objs = self.data_m.get_many(limit=1)
        self.assertEqual(1, len(objs))


if __name__ == '__main__':
    unittest.main()
