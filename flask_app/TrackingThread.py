import os
import queue
import sqlite3
import threading
import time
import psutil
import copy
import time

tracker_queue = queue.Queue()


class Settings:

    def __init__(self, max_extra_time, loop_time, game_objs):
        self.tracking_games = game_objs
        self.extra_time = max_extra_time
        self.loop_time = loop_time
        self.db_loc = None

    def game_lower_names(self):
        return [game.name for game in self.tracking_games]

    @classmethod
    def get_base_loc(cls, dir_name):
        cur_dir = os.getcwd().split("/")

        try:
            index = cur_dir.index(dir_name)
        except ValueError:
            return None

        return "/".join(cur_dir[0:index + 1])


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

    @classmethod
    def from_dict(cls, attrs):
        game_obj = GameObject("", 0, 0, 0)
        for key, value in attrs.items():
            setattr(game_obj, key, value)
        return game_obj

    def has_time(self):
        return time.time() < self.start_time + self.max_time

    def kill(self):
        for pid in self.PIDS:
            try:
                psutil.Process(pid).kill()
                self.PIDS.pop(pid)
            except psutil.NoSuchProcess:
                print(f"Tried to kill process {pid} that did not exist")
        print(f"Killed {self.name}")

    def start_now(self):
        self.start_time = int(time.time())

    def end_now(self):
        self.end_time = int(time.time())

    def update(self, new_state):
        if self == new_state:
            self.end_time = new_state.end_time
            self.max_time = new_state.max_time
            self.PIDS = new_state.PIDS

    # TODO add test
    def is_valid(self):
        name = self.name is not None and type(self.name) is str
        max_time = self.max_time is not 0 and type(self.max_time) is int
        start_time = type(self.start_time) is int
        end_time = type(self.end_time) is int

        return name and max_time and start_time and end_time

    def __eq__(self, other):
        if isinstance(other, GameObject):
            return self.name == other.name
        return False

    def deep_equal(self, other_obj):
        pids_equal = other_obj.PIDS == self.PIDS
        name_equal = other_obj.name == self.name
        is_running_equal = other_obj.is_running == self.is_running
        start_time_equal = other_obj.start_time == self.start_time
        end_time_equal = other_obj.end_time == self.end_time
        max_time_equal = other_obj.max_time == self.max_time

        return pids_equal and name_equal and is_running_equal and start_time_equal and end_time_equal and max_time_equal

    def __str__(self):
        return f"{self.name} --- {self.PIDS}"


class DataManager:

    def __init__(self, Settings):
        self.settings = Settings


    # TODO figure out how to pass the settings in the class/static instance
    @classmethod
    def get_db(cls, db_loc):
        db = sqlite3.connect(db_loc, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        return db

    class GetData:
        def __init__(self, dm):
            self.db = dm.get_db()

        def __enter__(self):
            return self.db

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.db.close()

    class StoreData:
        def __init__(self, dm):
            self.db = dm.get_db()

        def __enter__(self, dm):
            return self.db

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.db.commit()
            self.db.close()

    # TODO add test
    @classmethod
    def to_obj(cls, db_result):
        game_obj = GameObject.from_dict(db_result)
        if game_obj.is_valid():
            return game_obj
        else:
            return None

    # TODO add test
    @classmethod
    def get(cls, **query_params):
        with cls.GetData() as db:
            chain_where = ""

            # Goes through filtering params and adds them to the chain
            filter_count = 0
            for key, value in query_params:
                chain_where += f" {key}={value} AND"
                if filter_count != len(query_params.keys()):
                    chain_where += " AND"

                filter_count += 1

            DataManager.GetData.query(f"SELECT * FROM game_log WHERE {chain_where} LIMIT 1;")

    @classmethod
    def query(cls, query):
        with DataManager.GetData(cls) as db:
            conn = db.cursor()
            conn.execute(query)
            result = conn.fetchall()

    @classmethod
    def store_new(cls, game_obj):
        if isinstance(game_obj, GameObject):
            with cls() as db:
                c = db.cursor()
                command = f"INSERT INTO game_log (game_name, start_time, end_time, max_time) VALUES('{game_obj.name}', {int(game_obj.start_time)}, {int(game_obj.end_time)}, {int(game_obj.max_time)})"
                c.execute(command)


# Update a game object's end time
# Get a game object from the database


class CurrentState:
    def __init__(self, SettingsClass):
        self.currently_running = []
        self.settings = SettingsClass

    def add_to_running(self, game):
        if game not in self.currently_running:
            self.currently_running.append(game)

    def remove_from_running(self, game):
        index = self.get_game_index_running(game)
        if index is not None:
            del self.currently_running[index]

    def get_game_from_running(self, other_game_obj):
        index = self.get_game_index_running(other_game_obj)
        if index is not None:
            return self.currently_running[index]
        else:
            return None

    def get_game_index_running(self, other_game_obj):
        if other_game_obj in self.currently_running:
            return self.currently_running.index(other_game_obj)
        return None

    def game_start(self, game):
        self.add_to_running(game)
        index = self.get_game_index_running(game)
        self.currently_running[index].start_now()
        # TODO add storage capability

    def game_end(self, game):
        self.remove_from_running(game)
        game.end_now()
        # TODO add storage capability

    def game_update(self, old_status, new_status):
        if old_status.name != new_status.name:
            raise ValueError("The games do not match!")

        old_status.update(new_status)

    def update_running(self):
        while tracker_queue.empty() is False:
            new_state = tracker_queue.get()
            old_state = self.get_game_from_running(new_state)

            if old_state is not None:
                if self.has_any_diff(old_state, new_state) is False:
                    if new_state.is_running is False:
                        self.game_end(old_state)
                    continue

                if self.has_run_diff(old_state, new_state):
                    # print(f"Has a run state diff {old_state.is_running} and {new_state.is_running}")

                    if old_state.is_running:  # if old status is running, new one isn't apply game end changes
                        # print("Ending game")
                        self.game_end(old_state)

                if self.has_pid_diff(old_state, new_state):
                    old_state.update(new_state)

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
    daemon = True

    def __init__(self, SettingsClass):
        threading.Thread.__init__(self)
        self.loop_time = SettingsClass.loop_time
        self.current_state = SettingsClass.tracking_games

    def run(self):
        print("Starting tracking thread!\n")
        while True:
            self.update_status()
            time.sleep(self.loop_time)

    def update_status(self):
        # Resets the PIDS for all the game objects to update them
        self.reset_pids()
        self.get_curr_state()
        self.add_to_tracker_q()

    def get_curr_state(self):
        # iterate through processes
        for process in psutil.process_iter(attrs=['name', 'pid']):
            process_name = process.info['name'].lower()

            for new_game in self.current_state:
                # if processName contains game_name
                if new_game.name.lower() in process_name:
                    new_game.PIDS.append(process.info['pid'])

        for game in self.current_state:
            # if num pids is 0, is not running
            if len(game.PIDS) == 0:
                game.is_running = False
                # print("%s is closed" % game.name)
            else:
                game.is_running = True

        """for game in self.state:
            print(f"{game.name} has been found with pids: {game.PIDS}")"""

    def add_to_tracker_q(self):
        for game in self.current_state:
            tracker_queue.put(copy.deepcopy(game))

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
        self.update_block(state)
        self.enforce_block(state)

    def block(self, game):
        if game.name not in self.blocked_names():
            self.blocked_games.append(game)

    def blocked_names(self):
        return [game.name for game in self.blocked_games]

    def update_block(self, state):
        for game in state.currently_running:
            if game.has_time() is False:
                self.block(game)

    def enforce_block(self, state):
        for game in state.currently_running:
            if game.name in self.blocked_names():
                game.kill()
                state.remove_from_running(game)


def start_tracking():
    calculator = GameObject.min_init("Calculator", 5)
    # chrome = GameObject.min_init("Chrome", 5)
    discord = GameObject.min_init("Discord", 5)

    settings = Settings(1, 5, calculator, discord)

    tracker = Tracker(settings)
    current_state = CurrentState(settings)
    manager = GameManager()

    print("Starting...")
    tracker.start()
    while True:
        """print(current_state.currently_running)
        now = datetime.now().strftime("%c")
        print(f"------ {now} ------")"""
        current_state.update_running()
        manager.run(current_state)
        time.sleep(settings.loop_time)
        # print("\n")


if __name__ == '__main__':
    start_tracking()
