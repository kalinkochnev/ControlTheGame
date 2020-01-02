import queue
import psutil
import time
import re
import threading
import tkinter

namesOfGames = ['calculator', 'discord']

GamesTracking = []
runningGames = []
timeLimit = 100
timePause = 10

commandQueue = queue.Queue()
dataTransfer = queue.Queue()





class GameObject:

    def __init__(self, game_name, elapsed_time, status, game_pids):
        self.game_name = game_name
        self.game_pids = game_pids
        self.elapsed_time = elapsed_time
        self.status = status

    def update_pids(self):
        currentPids = []
        # iterate through processes
        for process in psutil.process_iter(attrs=['name', 'pid']):
            # if processName contains game_name
            if self.game_name.lower() in process.info['name'].lower():
                # get pid of process and add to currentPids list
                currentPids.append(process.info['pid'])
                self.status = 'running'
                print("%s has been found with pid: %s" % (self.game_name, process.info['pid']))
                self.game_pids = currentPids
        # if num pids is 0, status = closed
        if len(currentPids) == 0:
            status = 'closed'
            print("%s is closed" % self.game_name)

    def get_pids(self):
        return self.game_pids

    def clear_pids(self):
        self.game_pids = []
        self.status = "closed"

    def kill_game(self):
        for pid in self.game_pids:
            try:
                psutil.Process(pid).kill()
            except psutil.NoSuchProcess:
                print("Tried to kill process that did not exist")
            self.game_pids.remove(pid)

    def inc_game_runtime(self, timeToIncrease):
        self.elapsedTime += timeToIncrease

    def get_status(self):
        return self.status

    def get_name(self):
        return self.game_name


"""
TODO when a variable gets updated by the while loop it gets updated by the gui as well
     it currently does not update until a button is clicked by the user in the gui
"""


class GUI():
    def __init__(self):
        self.GameManager = tkinter.Tk()

        self.games_list = []
        self.time_limit = 0

        tkinter.Label(self.GameManager, text="Time to Add:").grid(row=0, column=0)
        self.time_entry = tkinter.Entry(self.GameManager)
        self.time_entry.grid(row=0, column=1)

        def addTime():
            user_input = self.time_entry.get()
            if re.search("\d+$", user_input) != None:
                self.sendCommand("add time", int(user_input))

        def killAll():
            self.sendCommand("stopall", "")

        self.add_time = tkinter.Button(self.GameManager, text="Add time", width=50, command=addTime)
        self.add_time.grid(row=1, columnspan=2)

        self.close_games = tkinter.Button(self.GameManager, text="Close all", width=50, command=killAll)
        self.close_games.grid(row=2, columnspan=2)

        tkinter.Label(self.GameManager, text="").grid(row=3)
        tkinter.Label(self.GameManager, text="Currently Running Games:").grid(row=4, column=0)

        self.games_list = tkinter.Message(self.GameManager, width=100, text="")
        self.games_list.grid(row=5, columnspan=2)

        tkinter.Label(self.GameManager, text="").grid(row=6, columnspan=2)
        tkinter.Label(self.GameManager, text="Total Running Time").grid(row=7, column=0)

        self.time_limit = tkinter.Label(self.GameManager, text="0")
        self.time_limit.grid(row=7, column=1)

    def refreshData(self):
        while not dataTransfer.empty():
            data = dataTransfer.get()
            self.time_limit = data['time limit']
            self.games_list = data['games list']
            print(data)

    def show(self):
        self.GameManager.mainloop()

    def sendCommand(self, name, info):
        commandQueue.put({name: info})
        print("command %s was sent" % (name))


def command_interface():
    global timeLimit
    print("Welcome to the game manager!")
    print("1.   add time [time in minutes]")
    print("2.   close all")
    print("Please input your commands:")
    while True:
        # gets user input and checks it against the regex for the command
        userInput = input()
        if re.search("^add time{1} \d+", userInput) != None:
            increaseBy = re.findall('\d+', userInput)
            commandQueue.put({'add time': int(increaseBy[0])})
        elif re.search("^close all{1}", userInput) != None:
            for game in runningGames:
                commandQueue.put({'stop': game.get_pids()})


def foobar():
    processes = psutil.process_iter(attrs=['name', 'pid'])
    return processes


def get_command(func):
    try:
        command = commandQueue.get_nowait()
        return func(command)
    except queue.Empty:
        print("None")


def choose_command(func, command):
    if 'stop' in command:
        return func(stop)
    if 'stop all' in command:
        return func(stop_all)
    if 'add time' in command:
        return func(add_time)


def execute_command(func):
    func()
    print(f'{func} was executed')


def stop(data):
    # stop based on the name of the process
    for game in runningGames:
        if command['stop'] == game.get_name():
            game.kill_game()


def stop_all(data):
    for game in runningGames:
        game.kill_game()


def add_time(data):
    timeLimit += command["add time"]
    print("The time was increased by %s minutes" % command['add time'])
    print(timeLimit)


def run_tracking_loop():
    # create array of objects for each game user wants to track
    for name in namesOfGames:
        GamesTracking.append(GameObject(name))
        # gets initial PID states for object
        GamesTracking[len(GamesTracking) - 1].get_pids()

    totalTime = 0
    while True:
        time.sleep(1)
        command_executor()

        # check if each item in gamesTracking is running
        for game in GamesTracking:
            game.update_pids()
            # if yes, add to running games
            if game.get_status() == "running" and game not in runningGames:
                runningGames.append(game)
            # if game not running, remove from runningGames.remove(game)ing games
            if game.get_status() == 'closed' and game in runningGames:
                runningGames.remove(game)
            game.inc_game_runtime(timePause)

        # check if total time is greater than runningGames.remove(game)imeLimit
        if totalTime > timeLimit and len(runningGames) > 0:
            # send command into queue to kill the running games
            commandQueue.put({"stopall": ""})

        totalTime += timePause
        gameNames = [game.get_name() for game in runningGames]
        print("Currently running games %s" % gameNames)

        # send data to gui
        data_tosend = {
            'time limit': timeLimit,
            'games list': gameNames,
        }
        dataTransfer.put(data_tosend)


if __name__ == "__main__":
    # create a command_interface and a command_executor thread
    """
    interfaceThread = threading.Thread(target=command_interface)
    interfaceThread.start()
"""
    trackingLoopThread = threading.Thread(target=run_tracking_loop, args=())
    trackingLoopThread.start()

    g = GUI()
    g.show()
