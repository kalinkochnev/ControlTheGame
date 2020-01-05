import queue
import threading
from datetime import datetime
import time
import psutil

from Exceptions import GamesDontMatch

tracker_queue = queue.Queue()


class Settings:

    def __init__(self, max_extra_time, *game_objs):
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

    @classmethod
    def min_init(cls, name, max_time_sec):
        return GameObject(name, 0, 0, max_time_sec)

    def kill(self):
        for pid in self.PIDS:
            try:
                psutil.Process(pid).kill()
            except psutil.NoSuchProcess:
                print(f"Tried to kill process {pid} that did not exist")
            #self.PIDS.remove(pid)
        print(f"Killed {self.name}")

    def __eq__(self, other):
        if isinstance(other, GameObject):
            return self.name == other.name
        return False

    def start_now(self):
        self.start_time = time.time()

    def end_now(self):
        self.end_time = time.time()

    def update(self, new_state):
        self.start_time = new_state.start_time
        self.end_time = new_state.end_now
        self.max_time = new_state.max_time
        self.PIDS = new_state.PIDS

    def __str__(self):
        return f"Game {self.PIDS} --- {self.PIDS}"


class DataManager:

    @classmethod
    def log(cls, game_obj):
        pass


class CurrentState(Settings):

    def __init__(self, SettingsClass):
        super().__init__(SettingsClass.extra_time, *SettingsClass.tracking_games)
        self.currently_running = []

    def add_to_running(self, game):
        self.currently_running.append(game)

    def remove_from_running(self, game):
        index = self.get_game_index_running(game)
        print(f"Killing calc at index: {index}")
        del self.currently_running[index]

    def get_game_from_running(self, other_game_obj):
        for game in self.currently_running:
            if game == other_game_obj:
                return game
        return None

    def get_game_index_running(self, game_obj):
        if game_obj in self.currently_running:
            return self.currently_running.index(game_obj)
        return None

    def get_game_index_running(self, game_obj):
        if game_obj in self.currently_running:
            return self.currently_running.index(game_obj)
        return None

    def game_start(self, not_in_running):
        self.add_to_running(not_in_running)
        index = self.get_game_index_running(not_in_running)
        self.currently_running[index].start_now()
        DataManager.log(self.currently_running[index])

    def game_end(self, game_in_running):
        self.remove_from_running(game_in_running)
        game_in_running.end_now()
        DataManager.log(game_in_running)

    def game_update(self, old_status, new_status):
        index = self.currently_running.index(old_status)
        self.currently_running[index].update(new_status)

    # TODO find out why old state gets cleared when it's deleted, probably something to do with get game index only doing it on currently running
    def update_running(self):
        while tracker_queue.empty() is False:
            new_state = tracker_queue.get()
            old_state = self.get_game_from_running(new_state)

            if old_state is not None:
                if self.has_any_diff(old_state, new_state) is False:
                    continue

                if self.has_run_diff(old_state, new_state):
                    if old_state.is_running:  # if old status is running, new one isn't apply game end changes
                        self.game_end(old_state)
                    else:  # if old status is not running, new one is, apply game start changes
                        self.game_start(new_state)
                elif self.has_pid_diff(old_state, new_state):
                    if len(new_state.PIDS) == 0:
                        self.remove_from_running(old_state)
                    else:
                        self.game_update(old_state, new_state)
            else:
                if len(new_state.PIDS) > 0:
                    self.game_start(new_state)

    def has_any_diff(self, old, new):
        return self.has_run_diff(old, new) or self.has_pid_diff(old, new)

    def has_run_diff(self, old_state, new_state):
        return old_state.is_running != new_state.is_running

    def has_pid_diff(self, old_state, new_state):
        return old_state.PIDS != new_state.PIDS


class Tracker(threading.Thread):

    def __init__(self, SettingsClass):
        threading.Thread.__init__(self)
        self.current_state = SettingsClass.tracking_games

    def run(self):
        print("Starting tracking thread!\n")
        while True:
            self.update_status()
            time.sleep(10)

    def update_status(self):
        # Resets the PIDS for all the game objects to update them
        self.reset_pids()
        self.get_curr_state()
        self.add_to_tracker_q()

    def get_curr_state(self):
        # iterate through processes
        for process in psutil.process_iter(attrs=['name', 'pid']):
            process_name = process.info['name'].lower()

            for index, new_game in enumerate(self.current_state):
                # if processName contains game_name
                if new_game.name.lower() in process_name:
                    self.current_state[index].PIDS.append(process.info['pid'])

                    # TODO come up with better way to assign values to item in list
                    # if num pids is 0, is not running
                    if len(new_game.PIDS) == 0:
                        self.current_state[index].is_running = False
                        print("%s is closed" % new_game.name)
                    elif new_game.is_running is False:
                        self.current_state[index].is_running = True

        """for game in self.current_state:
            print(f"{game.name} has been found with pids: {game.PIDS}")"""

    def add_to_tracker_q(self):
        for game in self.current_state:
            tracker_queue.put(game)

    def reset_pids(self):
        if self.current_state:
            for game in self.current_state:
                game.PIDS = []

    def game_from_name(self, name):
        for game in self.current_state:
            if name.lower() == game.name.lower():
                return game
        return None


class GameManager:
    blocked_games = []

    def run(self, state):
        if not self.update_block(state):
            self.enforce_block(state)

    @classmethod
    def kill_game(cls, game):
        game.kill()

    def is_out_of_time(self, game):
        return game.start_time + game.max_time <= time.time()

    def add_to_blocked(self, game):
        self.blocked_games.append(game)

    def blocked_game_names(self):
        return [game.name for game in self.blocked_games]

    def update_block(self, state):
        for game in state.currently_running:
            if self.is_out_of_time(game) and game not in self.blocked_games:
                self.add_to_blocked(game)
                return False
        return True

    def enforce_block(self, state):
        for game in state.currently_running:
            if game.name in self.blocked_game_names():
                self.kill_game(game)
                print("Resistance is futile!")


if __name__ == '__main__':
    calculator = GameObject.min_init("Calculator", 5)
    chrome = GameObject.min_init("chrome", 500)
    settings = Settings(1, calculator, chrome)

    tracker = Tracker(settings)
    tracker.start()

    current_state = CurrentState(settings)
    manager = GameManager()

    print("Starting...")
    while True:
        current_state.update_running()
        print(current_state.currently_running)
        manager.run(current_state)
        time.sleep(3)

