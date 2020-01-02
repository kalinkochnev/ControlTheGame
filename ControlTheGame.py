import queue
import threading
from datetime import datetime

import psutil

tracker_queue = queue.Queue()


class Settings:

    def __init__(self, max_extra_time, **game_objs):
        self.tracking_games = game_objs
        self.extra_time = max_extra_time

    def game_lower_names(self):
        return [game.name for game in self.tracking_games]


class GameObject:

    def __init__(self, name, start_time, end_time, max_time):
        self.PIDS = []
        self.is_running = False
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.max_time = max_time

    def kill(self):
        for pid in self.PIDS:
            try:
                psutil.Process(pid).kill()
            except psutil.NoSuchProcess:
                print(f"Tried to kill process {pid} that did not exist")
            self.PIDS.remove(pid)

    def __eq__(self, other):
        if isinstance(other, GameObject):
            return self.name == other.name
        return False


class DataManager:

    @classmethod
    def store(cls, game_obj):
        pass


class CurrentState(Settings):

    def __init__(self, SettingsClass):
        super().__init__(SettingsClass.extra_time, **SettingsClass.tracking_games)
        self.currently_running = []

    def get_from_q(self):
        if tracker_queue.qsize() >= 1:
            return tracker_queue.get()
        return None

    def detect_state_change(self):
        for updated_game in self.get_all_from_q():
            pass
        # If the game is not in currently running, add it
        # else if the PIDS changed update the previous game's pids
            # If is_running changed from false to True
                # update start_time to now()
                # store change
            # If is_running changed from true to false
                # update end_time to now()
                # store change

    def get_game_from_running(self, other_game_obj):
        for game in self.currently_running:
            if game == other_game_obj:
                return game
        return None


class Tracker(Settings):

    def __init__(self, SettingsClass):
        super().__init__(SettingsClass.extra_time, **SettingsClass.tracking_games)
        self.previous_state = self.tracking_games
        self.new_state = []

    def update_status(self) -> None:
        # Resets the PIDS for all the game objects to update them
        self.reset_pids()

        # Iterates through game objects
        for game_obj in self.tracking_games:

            # iterate through processes
            for process in psutil.process_iter(attrs=['name', 'pid']):
                # if processName contains game_name
                process_name = process.info['name']
                game_obj = self.game_from_name(process_name)

                if game_obj is not None:
                    game_obj.PIDS.append(process.info['pid'])

                    if not game_obj.is_running:
                        game_obj.is_running = True

                    # get pid of process and add to currentPids list
                    game_obj.PIDS.append(process.info['pid'])
                    print("%s has been found with pid: %s" % (self.game_name, process.info['pid']))

            # if num pids is 0, is not running
            if len(game_obj.PIDS) == 0:
                game_obj.is_running = False
                print("%s is closed" % self.game_name)

    def reset_pids(self) -> None:
        for game in self.tracking_games:
            game.PIDS = []

    def game_from_name(self, name):
        for game in self.tracking_games:
            if name.lower() == game.name.lower():
                return game
        return None


class GameManager:
    pass


if __name__ == '__main__':
    pass
