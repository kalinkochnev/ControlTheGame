import time
import unittest
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from flask_app.TrackingThread import GameObject, DataManager, Settings, Tracker, CurrentState


class TestDataManager(unittest.TestCase):
    def setUp(self) -> None:
        self.base_loc = Settings.get_base_loc("ControlTheGame")
        self.db_loc = ""
        self.init_test_db()

        self.game_obj1 = GameObject.min_init("game1", 1)
        self.game_obj2 = GameObject.min_init("game2", 1)
        self.settings = Settings(5, 1, [self.game_obj1, self.game_obj2])
        self.settings.db_loc = self.db_loc
        self.data_m = DataManager()
        Settings.testing = True

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
            db = DataManager.get_db_test()
            db.executescript(script.read().strip())

    def test_db_creation(self):
        self.assertTrue(os.path.exists(self.db_loc))

    def test_store_game_obj(self):
        start = 0
        game_obj = GameObject("test game", start, start + 1000, 2000)
        self.data_m.store_new(game_obj)
        result = self.data_m.query("SELECT * FROM game_log WHERE name='test game' LIMIT 1;", single=True)

        self.assertEqual(game_obj.name, result['name'])
        self.assertEqual(int(game_obj.start_time), result['start_time'])
        self.assertEqual(int(game_obj.end_time), result['end_time'])
        self.assertEqual(int(game_obj.time_remaining), result['time_remaining'])

    def test_to_obj(self):
        game_obj = GameObject("test game", time.time(), time.time() + 1000, 2000)
        self.data_m.store_new(game_obj)
        result = self.data_m.query("SELECT * FROM game_log WHERE name='test game' LIMIT 1;", single=True)
        to_obj = self.data_m.to_obj(result)
        self.assertTrue(game_obj.deep_equal(to_obj))

    def test_get(self):
        game_obj = GameObject("game", 0, 100, 10)
        game_obj1 = GameObject("game1", 0, 100, 10)

        self.data_m.store_new(game_obj)
        self.data_m.store_new(game_obj1)

        with patch("flask_app.TrackingThread.DataManager.query") as patched:
            query = "SELECT * FROM game_log WHERE time_remaining=10 AND name='game' LIMIT 1;"
            self.data_m.get(time_remaining=10, name="game")
            patched.assert_called_with(query, single=True)

            query = "SELECT * FROM game_log WHERE time_remaining=10 AND name='game' AND end_time=100 AND start_time=0 LIMIT 1;"
            self.data_m.get(time_remaining=10, name="game", end_time=100, start_time=0)
            patched.assert_called_with(query, single=True)

        self.assertIsNone(self.data_m.get())
        self.assertTrue(game_obj.deep_equal(self.data_m.get(name="game")))
        self.assertTrue(game_obj1.deep_equal(self.data_m.get(name="game1")))

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

    def test_date_range(self):
        base = datetime(2020, 11, 1)
        date1 = base + timedelta(days=2)
        date2 = base + timedelta(days=6)
        date3 = base + timedelta(days=8)

        game1 = GameObject("game1", base.timestamp(), base.timestamp() + 350, 200)
        game2 = GameObject("game2", date1.timestamp(), date1.timestamp() + 534, 2300)
        game3 = GameObject("game3", date2.timestamp(), date2.timestamp() + 1000, 23)
        game4 = GameObject("game1", date3.timestamp(), date3.timestamp() + 23, 200)
        self.data_m.store_many(game1, game2, game3, game4)

        results = self.data_m.get_date_range(base, base + timedelta(days=3))
        self.assertEqual([game1, game2], results)

        results = self.data_m.get_date_range(date1, base + timedelta(days=3))
        self.assertEqual([game2], results)

        results = self.data_m.get_date_range(date1, base + timedelta(days=7))
        self.assertEqual([game2, game3], results)

        results = self.data_m.get_date_range(date1, base + timedelta(days=7), name="game3")
        self.assertEqual([game3], results)

        results = self.data_m.get_date_range(base, base + timedelta(days=9), name="game1")
        self.assertEqual([game1, game4], results)

        results = self.data_m.get_date_range(base, base + timedelta(days=8))
        self.assertEqual([game1, game2, game3, game4], results)

    def test_get_day(self):
        base = datetime(2020, 11, 1)
        date1 = base + timedelta(days=2)
        date2 = base + timedelta(days=6)

        game1 = GameObject("game1", base.timestamp(), base.timestamp() + 350, 200)
        game2 = GameObject("game2", date1.timestamp(), date1.timestamp() + 534, 2300)
        game3 = GameObject("game3", date2.timestamp(), date2.timestamp() + 1000, 23)
        game4 = GameObject("game1", base.timestamp(), base.timestamp() + 350, 200)
        self.data_m.store_many(game1, game2, game3, game4)

        day_results = self.data_m.get_day(base)
        self.assertEqual([game1, game4], day_results)

        day_results = self.data_m.get_day(date1)
        self.assertEqual([game2], day_results)

        day_results = self.data_m.get_day(base, name="game1")
        self.assertEqual([game1, game4], day_results)

    def test_id_of_obj(self):
        self.data_m.store_new(self.game_obj1)
        self.assertEqual(1, self.data_m.id_of_obj(self.game_obj1))

    def test_update_game(self):
        game = GameObject.min_init("game", 1)
        self.data_m.store_new(game)
        db_id = self.data_m.id_of_obj(game)

        self.data_m.update_game(db_id, time_remaining=100, name="ay")
        stored = self.data_m.get(id=db_id)
        self.assertEqual(100, stored.time_remaining)
        self.assertEqual('ay', stored.name)

    # Tracker could not find any games for the day, starts new log
    def test_Tracker_load_data_empty(self):
        track1 = GameObject("Overwatch", 0, 0, 1000)
        track2 = GameObject("Counterstrike", 0, 0, 1000)
        settings = Settings(0, 1, [track1, track2])
        tracker = Tracker(settings)
        tracker.load_day_data()

        # No data in database
        self.assertEqual([track1, track2], tracker.current_state)
        tracker = Tracker(settings)

        # Data in db but not same day
        prev_day = datetime(2019, 10, 1)
        old_log1 = GameObject("Overwatch", prev_day.timestamp(), prev_day.timestamp() + 10, 10)
        old_log2 = GameObject("Counterstrike", prev_day.timestamp() + 1000, prev_day.timestamp() + 6573, 10)
        self.data_m.store_many(old_log1, old_log2)
        tracker.load_day_data()
        self.assertEqual([track1, track2], tracker.current_state)

    # Tracker found logged game data for that day
    def test_Tracker_load_data_existing(self):
        track1 = GameObject("Overwatch", 0, 0, 1000)
        track2 = GameObject("Counterstrike", 0, 0, 1000)
        settings = Settings(0, 1, [track1, track2])
        tracker = Tracker(settings)
        base_time = datetime.today().timestamp()

        game1 = GameObject("Overwatch", base_time, base_time + 500, 500)
        game2 = GameObject("Counterstrike", base_time + 1000, base_time + 1000 + 500, 500)
        game1b = GameObject("Overwatch", base_time + 3000, base_time + 3000 + 200, 300)
        game2b = GameObject("Counterstrike", base_time + 5000, base_time + 5000 + 500, 10)
        game1c = GameObject("Overwatch", base_time + 7000, base_time + 7000 + 10, 1)
        self.data_m.store_many(game1, game2, game1b, game2b, game1c)

        tracker.load_day_data()
        self.assertEqual([game1c, game2b], tracker.current_state)
        self.assertEqual(5, self.data_m.id_of_obj(game1c))
        self.assertEqual(5, self.data_m.id_of_obj(game1c))
        self.assertEqual(None, tracker.current_state[1].db_id)
        self.assertEqual(None, tracker.current_state[0].db_id)
        self.assertEqual(0, tracker.current_state[0].start_time)
        self.assertEqual(0, tracker.current_state[1].start_time)
        self.assertEqual(0, tracker.current_state[0].end_time)
        self.assertEqual(0, tracker.current_state[1].end_time)
        self.assertEqual(1, tracker.current_state[0].time_remaining)
        self.assertEqual(10, tracker.current_state[1].time_remaining)

    def test_clean_invalid(self):
        unfinished_game = GameObject('game', time.time(), 0, 100)
        unfinished_game2 = GameObject('game1', time.time() + 5, 0, 250)
        self.data_m.store_many(unfinished_game, unfinished_game2)
        self.data_m.clean_invalid()

        games = self.data_m.get_many()
        self.assertEqual(50 + unfinished_game.start_time, games[0].end_time)
        self.assertEqual(125 + unfinished_game2.start_time, games[1].end_time)

    def test_CurrentState_game_start_db(self):
        state = CurrentState(self.settings)
        game1 = GameObject("game", time.time(), 0, 200)
        state.game_start(game1)

        result = self.data_m.get(name="game")
        self.assertTrue(game1.deep_equal(result))

    def test_CurrentState_game_end_db(self):
        state = CurrentState(self.settings)
        game1 = GameObject("game", time.time(), 0, 200)
        state.game_start(game1)
        state.game_end(game1)

        result = self.data_m.get(name="game")
        self.assertTrue(game1.deep_equal(result))
        self.assertIsNot(0, game1.end_time)


if __name__ == '__main__':
    unittest.main()
