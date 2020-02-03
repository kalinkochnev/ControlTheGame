import os
import queue
import sqlite3
import threading
import time
from datetime import datetime, timedelta

import psutil
import copy
import time

tracker_queue = queue.Queue()


class Settings:
    testing = False

    def __init__(self, max_extra_time, loop_time, game_objs):
        self.extra_time = max_extra_time
        self.loop_time = loop_time
        self.tracking_games = game_objs

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

    def __init__(self, name, start_time, end_time, time_remaining):
        self.db_id = None
        self.PIDS = []
        self.is_running = False
        self.name = name
        self.start_time = int(start_time)
        self.end_time = int(end_time)  # if end time isn't determined yet, is stored as 0 in db
        self.time_remaining = int(time_remaining)

    @classmethod
    def min_init(cls, name, time_remaining):
        return GameObject(name, 0, 0, time_remaining)

    @classmethod
    def from_dict(cls, attrs):
        if attrs is None:
            return None

        game_obj = GameObject("", 0, 0, 0)
        for key in attrs.keys():
            if key == "id":
                setattr(game_obj, f"db_{key}", attrs[key])
            setattr(game_obj, key, attrs[key])
        return game_obj

    def has_time(self):
        return time.time() < self.start_time + self.time_remaining

    def get_time_remaining(self):
        if self.end_time == 0:
            return self.time_remaining

        return self.time_remaining - (self.end_time - self.start_time)

    def kill(self):
        for pid in self.PIDS:
            try:
                psutil.Process(pid).kill()
            except psutil.NoSuchProcess:
                pass

            self.PIDS.remove(pid)

    def start_now(self):
        self.start_time = int(time.time())

    def end_now(self):
        self.end_time = int(time.time())

    def update(self, new_state):
        if self.name == new_state.name:
            self.db_id = new_state.db_id
            self.end_time = new_state.end_time
            self.time_remaining = new_state.time_remaining
            self.PIDS = new_state.PIDS

    def is_valid(self):
        name = self.name is not None and type(self.name) is str
        time_remaining = type(self.time_remaining) is int or type(self.time_remaining) is float
        start_time = type(self.start_time) is int or type(self.start_time) is float
        end_time = type(self.end_time) is int or type(self.end_time) is float

        return name and time_remaining and start_time and end_time

    # TODO add test
    def current_save(self):
        # TODO make database query for lowest value instead of all of them
        if self.is_first_time():
            game_inst = DataManager.get_day(datetime.today(), limit=None, name=self.name)

            time_min = (pow(10, 10), None)
            for g in game_inst:
                if g.time_remaining < time_min[0]:
                    time_min = (g.time_remaining, g)

            return GameObject.min_init(self.name, time_min[0])

    # TODO add test
    def is_first_time(self):
        game_inst = DataManager.get_day(datetime.today(), limit=None, name=self.name)
        if len(game_inst) is 0 and game_inst is not None:
            return True
        return False

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
        max_time_equal = other_obj.time_remaining == self.time_remaining

        return pids_equal and name_equal and is_running_equal and start_time_equal and end_time_equal and max_time_equal

    def __str__(self):
        return f"{self.name} --- STATUS: {self.is_running} --- PIDS: {self.PIDS}"


class DataManager:

    @classmethod
    def get_db_test(cls):
        db_loc = os.path.join(Settings.get_base_loc("ControlTheGame"), "flask_app/tests/test_resources/test_db.sqlite")
        db = sqlite3.connect(db_loc, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        return db

    @classmethod
    def get_db(cls):
        db_loc = os.path.join(Settings.get_base_loc("ControlTheGame"), "flask_app/instance/flaskr.sqlite")
        db = sqlite3.connect(db_loc, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        return db

    class GetData:
        def __init__(self, dm):
            if Settings.testing:
                self.db = dm.get_db_test()
            else:
                self.db = dm.get_db()

        def __enter__(self):
            return self.db

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.db.close()

    class StoreData:
        def __init__(self, dm):
            if Settings.testing:
                self.db = dm.get_db_test()
            else:
                self.db = dm.get_db()

        def __enter__(self):
            return self.db

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.db.commit()
            self.db.close()

    @classmethod
    def to_obj(cls, db_result):
        game_obj = GameObject.from_dict(db_result)
        if db_result is None:
            return None

        if game_obj.is_valid():
            return game_obj
        else:
            raise Exception("The game obj was invalid!")

    @classmethod
    def chain_where(cls, params):
        # Goes through filtering params and adds them to the chain
        filter_count = 0
        chain_where = ""

        for key, value in params.items():
            if type(value) is str:
                chain_where += f"{key}='{value}'"
            else:
                chain_where += f"{key}={value}"

            if filter_count != len(params.keys()) - 1:
                chain_where += " AND "

            filter_count += 1
        return chain_where

    @classmethod
    def get(cls, **query_params):
        if len(query_params.keys()) == 0:
            return None

        query = f"SELECT * FROM game_log WHERE {cls.chain_where(query_params)} LIMIT 1;"
        result = DataManager.query(query, single=True)
        return cls.to_obj(result)

    @classmethod
    def query(cls, query, single=False):
        with DataManager.GetData(cls) as db:
            try:
                conn = db.cursor()
                conn.execute(query)
                if single is True:
                    return conn.fetchone()
                else:
                    return conn.fetchall()
            except sqlite3.Error as e:
                print(f"An error occurred with the database: {e.args[0]}")

    @classmethod
    def store_new(cls, game_obj):
        if isinstance(game_obj, GameObject):
            if game_obj.is_valid():
                try:
                    with cls.StoreData(cls) as db:
                        c = db.cursor()
                        command = f"INSERT INTO game_log (name, start_time, end_time, time_remaining) VALUES('{game_obj.name}', {int(game_obj.start_time)}, {int(game_obj.end_time)}, {int(game_obj.time_remaining)})"
                        c.execute(command)
                except sqlite3.Error as e:
                    print(f"An error occurred with the database: {e.args[0]}")

    @classmethod
    def store_many(cls, *game_objects):
        query = f"INSERT INTO game_log (name, start_time, end_time, time_remaining) VALUES "
        rows = ""
        for game_obj in game_objects:
            if isinstance(game_obj, GameObject):
                if game_obj.is_valid():
                    rows += f"('{game_obj.name}', {game_obj.start_time}, {game_obj.end_time}, {game_obj.time_remaining}),"
                else:
                    raise Exception("The game object put in was not valid!")
        rows = rows[0:len(rows) - 1]

        if len(rows) == 0:
            return []

        try:
            with cls.StoreData(cls) as db:
                c = db.cursor()
                c.execute(query + rows + ";")
        except sqlite3.Error as e:
            print(f"An error occurred with the database: {e.args[0]}")

    @classmethod
    def get_many(cls, limit=5, **query_params):
        query = "SELECT * FROM game_log"

        if len(query_params) != 0:
            query += f" WHERE {cls.chain_where(query_params)}"

        if limit is not None and type(limit) is int:
            query += f" LIMIT {limit};"
        elif limit is None:
            query += ";"
        else:
            return []

        game_objs = []
        results = cls.query(query, single=False)
        for row in results:
            game_objs.append(cls.to_obj(row))

        return game_objs

    @classmethod
    def get_date_range(cls, start, end, limit=5, **query_params):
        epoch1 = start.timestamp()
        epoch2 = end.timestamp()

        query = ""
        if len(query_params.keys()) != 0:
            query = f"SELECT * FROM game_log WHERE start_time >= {epoch1} AND end_time <= {epoch2} AND {cls.chain_where(query_params)}"
        else:
            query = f"SELECT * FROM game_log WHERE start_time >= {epoch1} AND start_time <= {epoch2}"

        if limit is not None and limit is int:
            query += f" LIMIT {limit};"
        else:
            query += f";"

        game_objs = []
        results = cls.query(query, single=False)
        for row in results:
            game_objs.append(cls.to_obj(row))

        return game_objs

    @classmethod
    def get_day(cls, day, limit=5, **query_params):
        start = datetime(day.year, day.month, day.day)
        end = start + timedelta(hours=24)

        return cls.get_date_range(start, end, limit, **query_params)

    @classmethod
    def id_of_obj(cls, game_obj):
        obj = cls.get(start_time=game_obj.start_time)
        if obj is not None:
            return obj.db_id

    @classmethod
    def update_game(cls, id, **values):
        set_vals = ""
        count = 0
        for key, value in values.items():
            if type(value) is str:
                set_vals += f"{key}='{value}'"
            else:
                set_vals += f"{key}={value}"

            if count != len(values.keys()) - 1:
                set_vals += ", "

            count += 1

        command = f"UPDATE game_log SET {set_vals} WHERE id={id};"
        try:
            with cls.StoreData(cls) as db:
                conn = db.cursor()
                conn.execute(command)
        except sqlite3.Error as e:
            print(f"An error occurred with the database: {e.args[0]}")

    # Cleans nulls and 0 values where there shouldn't be
    @classmethod
    def clean_invalid(cls):
        invalid_end_values = cls.get_many(limit=None, end_time=0)
        for game in invalid_end_values:
            # End time is start time + half of time remaining, which is more fair than no time

            time_remaining = game.time_remaining - (game.time_remaining / 2)
            end_time = game.start_time + (game.time_remaining / 2)
            cls.update_game(game.id, end_time=end_time, time_remaining=time_remaining)


class CurrentState:
    def __init__(self, SettingsClass):
        self.currently_running = []
        self.settings = SettingsClass
        self.GM = GameManager(self)

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

    # TODO make tests
    def game_start(self, game):
        assert game.db_id is None

        self.add_to_running(game)
        index = self.get_game_index_running(game)
        self.currently_running[index].start_now()

        # store the change in the db
        game.time_remaining = game.get_time_remaining()
        DataManager.store_new(game)
        id = DataManager.id_of_obj(game)
        game.id = id

    # TODO make tests
    def game_end(self, game):
        self.remove_from_running(game)
        game.end_now()
        id = DataManager.id_of_obj(game)

        if id is not None:
            DataManager.update_game(id, end_time=game.end_time, time_remaining=game.get_time_remaining())

    def game_update(self, old_status, new_status):
        if old_status.name != new_status.name:
            raise ValueError("The games do not match!")

        old_status.update(new_status)

    def update_running(self):
        while tracker_queue.empty() is False:
            new_state = tracker_queue.get()
            old_state = self.get_game_from_running(new_state)

            if self.has_run_diff(old_state, new_state):
                if old_state is None:
                    if new_state.is_running:
                        # Start tracking game if there is time remaining from previous save or there is no save
                        last_save = new_state.current_save()
                        if last_save is None or last_save.get_time_remaining() > 0:
                            self.game_start(new_state)
                            continue
                else:
                    # if the old state was running but the new one isn't, end it
                    if old_state.is_running:
                        self.game_end(new_state)
                        continue

            if self.has_pid_diff(old_state, new_state) and old_state is not None:
                old_state.update(new_state)
                continue

        self.GM.run()


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
        self.settings = SettingsClass
        self.loop_time = self.settings.loop_time
        self.current_state = []

    # TODO add test for when data has null value for end time or time_left
    def load_day_data(self):
        DataManager.clean_invalid()
        for game in self.settings.tracking_games:
            if game.is_first_time():
                self.current_state.append(game.current_save())

        else:
            self.current_state.append(game)

    def run(self):
        print("Starting tracking thread!\n")
        self.load_day_data()
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
            else:
                game.is_running = True

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

    def __init__(self, status):
        self.status = status

    def run(self):
        self.update_block()
        self.enforce_block()

    def block(self, game):
        if game.name not in self.blocked_names():
            self.blocked_games.append(game)

    def blocked_names(self):
        return [game.name for game in self.blocked_games]

    def update_block(self):
        for game in self.status.currently_running:
            if game.has_time() is False:
                self.block(game)

    def enforce_block(self):
        for game in self.status.currently_running:
            if game.name in self.blocked_names():
                game.kill()
                self.status.remove_from_running(game)


def start_tracking():
    calculator = GameObject.min_init("Calculator", 5)
    discord = GameObject.min_init("Chrome", 5)

    settings = Settings(1, 1, [calculator, discord])

    tracker = Tracker(settings)
    current_state = CurrentState(settings)

    print("Starting...")
    tracker.load_day_data()
    while True:
        print(current_state.currently_running)
        tracker.update_status()
        current_state.update_running()
        time.sleep(settings.loop_time)


if __name__ == '__main__':
    start_tracking()
