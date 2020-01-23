import copy
import unittest
from flask_app.TrackingThread import GameObject, Settings, CurrentState, tracker_queue


class CurrentStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.game_obj1 = GameObject.min_init("game1", 0)
        self.game_obj2 = GameObject.min_init("game2", 0)
        self.settings = Settings(5, 1, [self.game_obj1, self.game_obj2])
        self.state = CurrentState(self.settings)

    def test_creation(self):
        self.assertEqual([], self.state.currently_running)

    def test_add_to_running(self):
        self.state.add_to_running(self.game_obj1)
        self.assertEqual([self.game_obj1], self.state.currently_running)

    def test_game_index_from_running(self):
        self.state.currently_running = [self.game_obj1, self.game_obj2]
        self.assertEqual(0, self.state.get_game_index_running(self.game_obj1))
        self.assertEqual(1, self.state.get_game_index_running(self.game_obj2))
    
    def test_game_from_running(self):
        self.state.currently_running = [self.game_obj1, self.game_obj2]
        output_game = self.state.get_game_from_running(self.game_obj1)
        self.assertEqual(self.game_obj1, output_game)

    def test_remove_from_running(self):
        self.state.currently_running = [self.game_obj1, self.game_obj2]
        self.state.remove_from_running(self.game_obj1)
        self.assertEqual([self.game_obj2], self.state.currently_running)

    def test_game_start(self):
        self.state.game_start(self.game_obj1)
        self.assertEqual([self.game_obj1], self.state.currently_running)
        self.assertNotEqual(0, self.game_obj1.start_time)

    def test_game_end(self):
        self.state.currently_running = [self.game_obj1, self.game_obj2]
        self.state.game_end(self.game_obj1)
        self.assertEqual([self.game_obj2], self.state.currently_running)
        self.assertNotEqual(0, self.game_obj1.end_time)

    def test_game_update(self):
        self.state.currently_running = [self.game_obj1, self.game_obj2]
        updated = GameObject("game1", 0, 30, 1)
        self.state.game_update(self.game_obj1, updated)
        self.assertEqual("game1", self.game_obj1.name)
        self.assertEqual(0, self.game_obj1.start_time)
        self.assertEqual(30, self.game_obj1.end_time)
        self.assertEqual(1, self.game_obj1.time_remaining)

        # Check that the reference in the list gets updated too
        index = self.state.get_game_index_running(self.game_obj1)
        self.assertTrue(self.game_obj1.deep_equal(self.state.currently_running[index]))

    # The game doesn't exist in running, but has no PIDS
    def test_update_no_exist(self):
        copy_game = copy.deepcopy(self.game_obj1)
        tracker_queue.put(copy_game)

        self.state.update_running()
        self.assertEqual([], self.state.currently_running)

    # The game already exists with pids but new is not running
    def test_update_already_exist(self):
        copy_game = copy.deepcopy(self.game_obj1)
        copy_game.is_running = False
        tracker_queue.put(copy_game)

        self.game_obj1.PIDS = [1, 2, 3]
        self.game_obj1.is_running = True
        self.state.currently_running = [self.game_obj1]

        self.assertEqual([self.game_obj1], self.state.currently_running)
        self.state.update_running()
        self.assertEqual([], self.state.currently_running)

    # Game already exists but has different PIDS
    def test_update_already_exists2(self):
        copy_game = copy.deepcopy(self.game_obj1)
        copy_game.PIDS = [1, 2, 3, 4]
        copy_game.is_running = True
        tracker_queue.put(copy_game)

        self.game_obj1.PIDS = [1, 2, 3]
        self.game_obj1.is_running = True
        self.state.currently_running = [self.game_obj1]
    
        self.assertEqual([self.game_obj1], self.state.currently_running)
        self.state.update_running()
        self.assertEqual([self.game_obj1], self.state.currently_running)
        self.assertEqual([1, 2, 3, 4], self.game_obj1.PIDS)

    # The game isn't currently running but in the new status it is
    def test_update_doesnt_exist(self):
        self.assertEqual([], self.state.currently_running)

        self.game_obj1.is_running = True
        self.game_obj1.PIDS = [1, 2, 3]
        tracker_queue.put(self.game_obj1)

        self.state.update_running()
        self.assertEqual([self.game_obj1], self.state.currently_running)

    def test_has_pid_diff(self):
        self.assertFalse(self.state.has_pid_diff(self.game_obj1, self.game_obj2))
        self.game_obj1.PIDS = [1, 2, 3]
        self.assertTrue(self.state.has_pid_diff(self.game_obj1, self.game_obj2))

    def test_has_run_diff(self):
        self.assertFalse(self.state.has_run_diff(self.game_obj1, self.game_obj2))
        self.game_obj1.is_running = True
        self.assertTrue(self.state.has_run_diff(self.game_obj1, self.game_obj2))

    def test_has_any_diff(self):
        self.assertFalse(self.state.has_any_diff(self.game_obj1, self.game_obj2))
        self.game_obj1.is_running = True
        self.assertTrue(self.state.has_any_diff(self.game_obj1, self.game_obj2))



if __name__ == '__main__':
    unittest.main()
