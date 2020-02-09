import os
import sqlite3
import time

import psutil


class Settings:
    testing = False
    tracked_programs = []
    loop_time = 0

    @classmethod
    def setup(cls, programs, loop_time, testing):
        Settings.tracked_programs = programs
        Settings.loop_time = loop_time
        Settings.testing = testing

    @classmethod
    def get_base_loc(cls, dir_name):
        cur_dir = os.getcwd().split("/")

        try:
            index = cur_dir.index(dir_name)
        except ValueError:
            return None

        return "/".join(cur_dir[0:index + 1])

# Is a stripped down program object to differentiate between running programs and given programs to track
class TrackedProgram:
    name = ""
    max_time = 0
    db_id = None

    # TODO create getters and setters that automatically round the numbers to integers
    start_time = 0
    end_time = 0
    time_remaining = max_time
    blocked = False

    def __init__(self, name, max_time, start, end, remaining):
        self.name = name
        self.max_time = max_time
        self.start_time = start
        self.end_time = end
        self.time_remaining = remaining

    @classmethod
    def program_from_dict(cls, attrs):
        if attrs is None:
            return None

        program = TrackedProgram("", 0, 0, 0, 0)
        for key in attrs.keys():
            if key == "id":
                setattr(program, f"db_{key}", attrs[key])
            setattr(program, key, attrs[key])
        return program

    @classmethod
    def min_init(cls, name, max_time):
        return TrackedProgram(name, max_time, 0, 0, 0)

    def start_now(self):
        self.start_time = time.time()

    def end_now(self):
        self.end_time = time.time()

    def update(self, program_obj):
        if self.start_time == 0:
            self.start_time = program_obj.start_time

        if self.end_time == 0:
            self.end_time = program_obj.end_time

        self.time_remaining = self.time_left()

        if self.time_remaining > 0:
            self.blocked = False
        else:
            self.blocked = True

    def time_left(self):
        time_remain = self.time_remaining - (self.end_time - self.start_time)
        if self.end_time == 0:
            return self.time_remaining
        elif time_remain < 0:
            return 0
        else:
            return time_remain

    def has_time(self):
        return time.time() < (self.start_time + self.time_remaining)

    def is_valid(self):
        name_valid = type(self.name) is str
        max_time_valid = type(self.max_time) is int or type(self.max_time) is float or self.max_time is None
        start_time_valid = type(self.start_time) is int or type(self.start_time) is float
        end_time_valid = type(self.end_time) is int or type(self.end_time) is float
        time_remaining_valid = type(self.time_remaining) is int or type(self.time_remaining) is float
        db_id_valid = type(self.db_id) is int
        return name_valid and max_time_valid and start_time_valid, end_time_valid, time_remaining_valid, db_id_valid

class CurrentlyRunning:
    currently_running = []
    program_objs = []

    def reset(self):
        self.currently_running = []
        self.program_objs = []

    def init_program_objs(self):
        for program in Settings.tracked_programs:
            pg_obj = Program(program)
            self.program_objs.append(pg_obj)

    def populate_program_pids(self):
        # iterate through processes
        for process in psutil.process_iter(attrs=['name', 'pid']):
            process_name = process.info['name'].lower()

            for program in self.program_objs:

                if program.name.lower() in process_name:
                    pid = process.info['pid']
                    program.add_pid(pid)

    def add_to_running(self):
        for pg in self.program_objs:
            if pg.is_running():
                self.currently_running.append(pg)

    def get_curr_running(self):
        self.reset()
        self.init_program_objs()
        self.populate_program_pids()
        self.add_to_running()
        return self.currently_running


# How the programs that are tracked will be represented
class Program(TrackedProgram):
    PIDS = []

    def __init__(self, tracked):
        super().__init__(tracked.name, tracked.max_time, tracked.start_time, tracked.end_time, tracked.time_remaining)

    def add_pid(self, pid):
        self.PIDS.append(pid)

    def reset_pids(self):
        self.PIDS = []

    def is_running(self):
        return len(self.PIDS) > 0


# Stores any changes made into the database
class DataManager:
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
    def to_obj(cls, db_result):
        program_obj = TrackedProgram.program_from_dict(db_result)
        if db_result is None:
            return None

        if program_obj.is_valid():
            return program_obj
        else:
            raise Exception("The program object was invalid!")

    @classmethod
    def chain_and_helper(cls, params):
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

    # store tracked program data
    @classmethod
    def log_started(cls, log_start):
        pass

    @classmethod
    def log_ended(cls, log_end):
        pass


class StateChangeDetector:
    prev_state = []
    curr_state = []

    def update_states(self, current_state):
        self.prev_state = self.curr_state
        self.curr_state = current_state

    def get_program(self, program, array):
        for item in array:
            if program.name == item.name:
                return item
        return None

    def is_stopped(self, new_state):
        old_state = self.get_program(new_state, self.prev_state)
        new_state = self.get_program(new_state, self.curr_state)

        # If old state is found, means it was running, if new state is not found that means its not running anymore
        return old_state is not None and new_state is None

    def is_started(self, new_state):
        old_state = self.get_program(new_state, self.prev_state)
        new_state = self.get_program(new_state, self.curr_state)
        return old_state is None and new_state is not None

    def get_started(self):
        started_pgs = []
        for item in self.curr_state:
            if self.is_started(item):
                started_pgs.append(item)
        return started_pgs

    def get_stopped(self):
        ended_pgs = []
        for item in self.curr_state:
            if self.is_stopped(item):
                ended_pgs.append(item)
        return ended_pgs


class StateLogger:
    program_states = None

    def __init__(self, program_states):
        self.program_states = program_state

    def log_started(self, to_log):
        self.set_starts(to_log)
        DataManager.log_started(to_log)
        program_state.updated_started(to_log)

    def log_end(self, to_log):
        self.set_ends(to_log)
        DataManager.log_ended(to_log)
        program_state.updated_ended(to_log)

    def set_starts(self, items):
        for item in items:
            item.start_now()

    def set_ends(self, items):
        for item in items:
            item.end_now()


class ProgramManager:
    blocked_programs = []

    def kill(self, program):
        for pid in program.PIDS:
            try:
                psutil.Process(pid).kill()
            except psutil.NoSuchProcess:
                pass
        program.reset_pids()

    def update_blocked(self, blocked):
        self.blocked_programs = blocked

    def is_blocked(self, program):
        blocked_names = [pg.name for pg in self.blocked_programs]
        return program.name in blocked_names

    def prune_programs(self, unclean_running):
        cleaned_running = []
        for program in unclean_running:
            if self.is_blocked(program):
                self.kill(program)
            else:
                cleaned_running.append(program)

        return cleaned_running


class ProgramStates:
    states = []

    def __init__(self, states):
        self.states = states

    def updated_started(self, started_pgs):
        for pg in started_pgs:
            pg_state = self.get_program(pg)
            pg_state.update(pg)

    def updated_ended(self, ended_pgs):
        for pg in ended_pgs:
            pg_state = self.get_program(pg)
            pg_state.update(pg)

    def get_program(self, pg):
        for program in self.states:
            if pg.name == program.name:
                return program
        return None

    def get_blocked(self):
        blocked = []

        for program in self.states:
            if program.blocked:
                blocked.append(program)

        return blocked


class LoadData:
    @classmethod
    def program_states(cls):
        pass

    # Load blocked data into PM
    # Loads initial states for program


if __name__ == '__main__':
    # Settings
    chrome = TrackedProgram.min_init("Chrome", 10)
    calculator = TrackedProgram.min_init("Calculator", 10)
    Settings.setup([chrome, calculator], 1, False)

    state_detector = StateChangeDetector()
    currently_running = CurrentlyRunning()
    program_manager = ProgramManager()

    # Loads initial data into program
    program_state = ProgramStates(LoadData.program_states())
    program_manager.update_blocked(program_state.get_blocked())
    logger = StateLogger(program_state)

    while True:
        # Removes programs that shouldn't be running
        running = currently_running.get_curr_running()
        pruned = program_manager.prune_programs(running)

        # State detector gets which games should be updated
        state_detector.update_states(pruned)
        started = state_detector.get_started()
        ended = state_detector.get_stopped()

        # Logger keeps ProgramStates and DB with most current info
        logger.log_end(ended)
        logger.log_started(started)

        # Update program manager with
        program_manager.update_blocked(program_state.get_blocked())
