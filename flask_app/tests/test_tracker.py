import time
import unittest
from unittest.mock import patch

from flask_app.TrackingThread import Settings, GameObject, Tracker, tracker_queue, DataManager


class TrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game_obj1 = GameObject.min_init("game1", 0)
        self.game_obj2 = GameObject.min_init("game2", 0)
        self.settings = Settings(0, 1, [self.game_obj1, self.game_obj2])
        self.tracker = Tracker(self.settings)
        self.tracker.load_day_data()

    def test_creation(self):
        self.assertEqual(1, self.tracker.loop_time)
        self.assertEqual([self.game_obj1, self.game_obj2], self.tracker.current_state)

    def test_game_from_name(self):
        self.assertEqual(self.game_obj1, self.tracker.game_from_name("game1"))

    def test_reset_PIDS(self):
        self.tracker.reset_pids()
        for game in self.tracker.current_state:
            with self.subTest():
                self.assertEqual([], game.PIDS)

    def test_get_current_state(self):
        self.assertFalse(self.game_obj1.is_running)
        self.assertFalse(self.game_obj2.is_running)

        with patch('flask_app.TrackingThread.psutil.process_iter') as mocked_process_iter:
            with patch('flask_app.TrackingThread.psutil.Process') as mocked_process:
                mocked_process.info = {"name": 'game1', "pid": 1}
                mocked_process_iter.asser_called_with(attrs=['name', 'pid'])
                mocked_process_iter.return_value = iter([mocked_process])

                self.tracker.get_curr_state()
                self.assertTrue(self.game_obj1.is_running)
                self.assertEqual([1], self.tracker.game_from_name("game1").PIDS)

                mocked_process.info = {"name": 'game2', "pid": 2}
                mocked_process_iter.return_value = iter([mocked_process])
                self.tracker.get_curr_state()
                self.assertTrue(self.game_obj2.is_running)
                self.assertEqual([2], self.tracker.game_from_name("game2").PIDS)

                mocked_process.info = {"name": 'game2blah', "pid": 3}
                mocked_process_iter.return_value = iter([mocked_process])
                self.tracker.get_curr_state()
                self.assertEqual([2, 3], self.tracker.game_from_name("game2").PIDS)

                mocked_process.info = {"name": 'game1poo', "pid": 4}
                mocked_process_iter.return_value = iter([mocked_process])
                self.tracker.get_curr_state()
                self.assertEqual([1, 4], self.tracker.game_from_name("game1").PIDS)

    def test_add_to_q(self):
        self.tracker.add_to_tracker_q()

        # Makes sure that they are not referenced to one another but same values
        item1 = tracker_queue.get()
        item2 = tracker_queue.get()
        self.assertFalse(item1 is self.game_obj1)
        self.assertFalse(item2 is self.game_obj2)
        self.assertTrue(self.game_obj1.deep_equal(item1))
        self.assertTrue(self.game_obj2.deep_equal(item2))


if __name__ == '__main__':
    unittest.main()
