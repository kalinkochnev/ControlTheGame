import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, call

import psutil

from flask_app.TrackingThread import GameObject


class GameObjectTests(unittest.TestCase):

    def test_creation(self):
        time = datetime.now()
        obj = GameObject("test", time, time + timedelta(seconds=5), 10)
        self.assertEqual(obj.start_time, time)
        self.assertEqual(obj.end_time, time + timedelta(seconds=5))
        self.assertEqual(obj.name, "test")
        self.assertEqual(obj.max_time, 10)

    def test_min_init(self):
        obj = GameObject.min_init("test", 5)
        self.assertEqual(obj.start_time, 0)
        self.assertEqual(obj.end_time, 0)
        self.assertEqual(obj.name, "test")
        self.assertEqual(obj.max_time, 5)

    def test_eq(self):
        obj1 = GameObject.min_init("gameA", 0)
        obj2 = GameObject.min_init("gameB", 0)
        self.assertNotEqual(obj1, obj2)
        obj3 = GameObject.min_init("gameA", 0)
        self.assertEqual(obj1, obj3)
        obj4 = GameObject.min_init("gameA", 1)
        self.assertEqual(obj1, obj4)

    def test_start_now(self):
        obj = GameObject.min_init("game", 0)
        obj.start_now()
        self.assertNotEqual(obj.start_time, 0)

    def test_end_now(self):
        obj = GameObject.min_init("game", 0)
        obj.end_now()
        self.assertNotEqual(obj.end_time, 0)

    def test_update(self):
        obj1 = GameObject.min_init("game1", 0)
        obj1.PIDS = [1, 2, 3]

        obj2 = GameObject("game1", 10, 20, 5)
        obj1.update(obj2)
        self.assertEqual(obj1.name, "game1")
        self.assertEqual(obj1.start_time, 10)
        self.assertEqual(obj1.end_time, 20)
        self.assertEqual(obj1.max_time, 5)
        self.assertEqual(obj1.PIDS, [])

    def test_kill_game(self):
        # test when pids do exist
        pid_list = [1, 2, 3, 10, 4]
        game1 = GameObject.min_init('game1', 100)

        with patch("flask_app.TrackingThread.psutil.Process.kill") as mocked_kill:
            mocked_kill.return_value = None
            game1.kill()

        self.assertEqual([], game1.PIDS)

    def test_kill_game_invalid_PID(self):
        # test when pids do exist
        pid_list = [1, 2, 3, 10, 4]
        game1 = GameObject.min_init('game1', 100)

        with patch("flask_app.TrackingThread.psutil.Process.kill") as mocked_kill:
            mocked_kill.side_effect = psutil.NoSuchProcess(None)
            game1.kill()


if __name__ == '__main__':
    unittest.main()
