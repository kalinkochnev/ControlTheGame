import sqlite3
import time
import unittest
import os

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
        self.data_m = DataManager(self.settings)
        self.db = self.data_m.get_db(self.db_loc)

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
            db = DataManager.get_db(self.db_loc)
            db.executescript(script.read().strip())

    def test_db_creation(self):
        self.assertTrue(os.path.exists(self.db_loc))

    def test_store_game_obj(self):
        conn = self.db.cursor()
        game_obj = GameObject("test game", time.time(), time.time() + 1000, 2000)
        self.data_m.store_new(game_obj)

        query = "SELECT * FROM game_log WHERE game_name='test game' LIMIT 1;"
        conn.execute(query)
        result = conn.fetchone()

        self.assertEqual(game_obj.name, result['game_name'])
        self.assertEqual(int(game_obj.start_time), result['start_time'])
        self.assertEqual(int(game_obj.end_time), result['end_time'])
        self.assertEqual(int(game_obj.max_time), result['max_time'])

    def test_game_obj_from_db(self):
        self.data_m.store_new(self.game_obj1)
        result = self.data_m.from_db(pk=1)
        self.assertTrue(self.game_obj1.deep_equal(result))


if __name__ == '__main__':
    unittest.main()
