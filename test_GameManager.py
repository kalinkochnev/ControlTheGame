import unittest
from unittest.mock import patch, call
import GameManager as GM
import psutil


class TestGameManager(unittest.TestCase):
    def test_kill_game(self):
        # test when pids do exist
        pid_list = [1, 2, 3, 10, 4]
        game1 = GM.GameObject('game1', 100, 'closed', pid_list)

        with patch("GameManager.psutil.Process.kill") as mocked_kill:
            mocked_kill.return_value = None
            game1.kill_game()
            calls = [call() for var in pid_list]
            mocked_kill.assert_has_calls(calls)

    def test_NoSuchProcess_kill_game(self):
        pid_list = [1, 2, 3, 10, 4]
        game1 = GM.GameObject('game1', 100, 'closed', pid_list)
        with patch("GameManager.psutil.Process.kill") as mocked_kill:
            mocked_kill.side_effect = psutil.NoSuchProcess(None)
            game1.kill_game()

    def test_update_pids(self):
        game1 = GM.GameObject('game1', 100, 'closed', [1, 2, 3, 10, 4])
        with patch('GameManager.psutil.process_iter') as mocked_process_iter:

            with patch('GameManager.psutil.Process') as mocked_process:
                mocked_process.info = {"name": 'game1', "pid": 10}
                mocked_process_iter.asser_called_with(attrs=['name', 'pid'])
                mocked_process_iter.return_value = iter([mocked_process])

                game1.update_pids()
                self.assertEqual(game1.game_pids, [10])

    def test_clear_pids(self):
        pid_list = [1, 2, 3, 10, 4]
        game1 = GM.GameObject('game1', 100, 'closed', pid_list)
        game1.clear_pids()
        self.assertEqual(game1.game_pids, [])

"""
    def test_get_info(self):
        #test a dict exists with keys "elapsed time", "status", "game pids", "game name"
        game_name, elapsed_time, status, game_pids = ('game1', 100, 'running', [1, 2, 3, 4, 5])
        testObj = GM.GameObject(game_name, elapsed_time, status, game_pids)
        obj_dict1 = {'game name': game_name, 'elapsed time':elapsed_time, 'status':status, 'game pids':game_pids}

        self.assertDictEqual(testObj.get_info(), obj_dict1)

    def test_update_gamelist(self):
        #create fake game objects with data
        #test with no games in list
        #test with games that have a closed status
        #test games that have running status
    def test_check_times(self):
        #test with total time > than time limit
        #test with total time < than time limit
        #test with total time == to time limit

    def test_get_command(self):
        #test get_command with empty Queue
        #test get_command with full Queue
        #test get_command with values in Queue
    def test_choose_command(self):
        self.assertEqual(GM.choose_command({'add time':0}), GM.add_time)
        self.assertEqual(GM.choose_command({'stop all':[]}), GM.stop_all)
        self.assertEqual(GM.choose_command({'stop':[1, 2, 3, 4]}), GM.stop)
        self.assertIsNone(GM.choose_command({}))
        #test the given a command string that correct game is chosen
    def test_execute_command(self):
        #test when command is stop the game is removed from array and status is changed to closed
        #test when command is stopall running_games array is empty and all the games have a status of closed
        #test when command is add time the games max_time is increased
"""
if __name__ == '__main__':
    unittest.main()
