class Settings:
    tracked_programs = []
    pass


# Is a stripped down program object to differentiate between running programs and given programs to track
class TrackedProgram:
    name = ""


class CurrentlyRunning:
    currently_running = []

    def get_running(self):
        pass

    # updates every x seconds with the currently running programs


# How the programs that are tracked will be represented
class Program(TrackedProgram):
    start_time = 0
    end_time = 0
    time_remaining = 0
    blocked = False
    PIDS = []


# Stores any changes made into the database
class DataManager:
    # store tracked program data
    pass


class StateChangeDetector:
    prev_state = []
    curr_state = []

    def update_states(self):
        pass

    def comp_program_states(self, program):
        pass

    def is_stopped(self, state1, state2):
        pass

    def is_started(self, state1, state2):
        pass

    def log_started(self):
        pass

    def log_stopped(self):
        pass


class StateLogger:
    def __init__(self, programstates):
        self.PS = programstates

    def log_new(self):
        pass

    def end_prev(self):
        pass


class ProgramManager:
    blocked_programs = []

    def can_run(self, program):
        pass

    def kill(self):
        pass

    def update_blocked(self, states):
        pass


class ProgramStates:
    states = []

    def update_program(self, program):
        pass

    def get_program(self, tracked_program):
        pass

    def get_states(self):
        pass


class LoadData:
    def program_states(self):
        pass

    # Load blocked data into PM
    # Loads initial states for program states
    pass
