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
commandQueue = queue.Queue()
timePause = 10

class GameObject():
    gameName = "" 
    gamePids = []
    elapsedTime = 0
    status = ""

    def __init__(self, gameName):
        self.gameName = gameName

    def update_pids(self):
        currentPids = []
        #iterate through processes
        for process in psutil.process_iter(attrs=['name', 'pid']):
            #if processName contains gameName
            if self.gameName.lower() in process.info['name'].lower():
                #get pid of process and add to currentPids list
                currentPids.append(process.info['pid'])
                self.status = 'running'
                print("%s has been found with pid: %s" % (self.gameName, process.info['pid']))
                self.gamePids = currentPids
        #if num pids is 0, status = closed
        if len(currentPids) == 0:
            status = 'closed'
            print("%s is closed" % self.gameName)

    def get_pids(self):
        return self.gamePids

    def clear_pids(self):
        self.gamePids = []

    def inc_game_runtime(self, timeToIncrease):
        self.elapsedTime += timeToIncrease

    def get_status(self):
        return self.status

    def get_name(self):
        return self.gameName


class GUI():
    def __init__(self):
        self.GameManager = tkinter.Tk()
        tkinter.Label(self.GameManager,text="Time to Add:").grid(row=0, column=0)
        self.time_entry = tkinter.Entry(self.GameManager)
        self.time_entry.grid(row=0, column=1)



        def addTime():
            user_input = self.time_entry.get()
            if re.search("\d+$", user_input) != None:
                self.sendCommand("add time", int(user_input))

        def killAll():
            for game in GamesTracking:
                self.sendCommand("stop",game.get_pids())


        self.add_time = tkinter.Button(self.GameManager, text="Add time", width=50, command=addTime)
        self.add_time.grid(row=1, columnspan=2)
        
        self.close_games = tkinter.Button(self.GameManager, text="Close all", width=50, command=killAll)
        self.close_games.grid(row=2,columnspan=2)
        

        tkinter.Label(self.GameManager,text="").grid(row=3)
        tkinter.Label(self.GameManager,text="Currently Running Games:").grid(row=4,column=0)
        self.games_list = tkinter.Message(self.GameManager, width=100,  text="")
        self.games_list.grid(row=5,columnspan=2)

        tkinter.Label(self.GameManager,text="").grid(row=6,columnspan=2)
        tkinter.Label(self.GameManager,text="Total Running Time").grid(row=7,column=0)

        self.running_time = tkinter.Label(self.GameManager,text="blag")
        self.running_time.grid(row=7,column=1)

    def setGameNames(self,games):
        gameNames = "\n".join(games)
        self.games_list['text'] = gameNames

    def setRunningTime(self,time):
        self.running_time['text'] = time 

    def show(self):    
        self.GameManager.mainloop()
    
    def sendCommand(self, name, info):
        commandQueue.put({name:info})
        print("command '%s' was sent with time %s"%(name, info))


def command_interface():
    global timeLimit
    print("Welcome to the game manager!")
    print("1.   add time [time in minutes]")
    print("2.   close all")
    print("Please input your commands:")
    while True:
        #gets user input and checks it against the regex for the command
        userInput = input()
        if  re.search("^add time{1} \d+", userInput) != None:
            increaseBy = re.findall('\d+', userInput)
            commandQueue.put({'add time' : int(increaseBy[0])})
        elif re.search("^close all{1}", userInput) != None:
            for game in runningGames:
                commandQueue.put({'stop' : game.get_pids()})


def command_executor():
    global timeLimit
    #executes commands put through the queue
    command = commandQueue.get()
    #checks if the dict key is the right one
    if "stop" in command:
        #loop through pids and kill them
        #TODO make sure it has pids to kill, if not find them
        for pid in command["stop"]:
            psutil.Process(pid).kill()
        """
        TODO
            -stop the running timer
            -store the session data somewhere
        """

    if "add time" in command:
        timeLimit += command["add time"]
        print("The time was increased by %s minutes" % command['add time'])
        print(timeLimit)


def runTrackingLoop(gui):
        #create array of objects for each game user wants to track
    for name in namesOfGames:
        GamesTracking.append(GameObject(name))
        #gets initial PID states for object
        GamesTracking[len(GamesTracking)-1].get_pids()

    totalTime = 0
    while True:
        time.sleep(timePause)
        command_executor()   

        #check if each item in gamesTracking is running
        for game in GamesTracking:
            game.update_pids()
            #if yes, add to running games
            if game.get_status() == "running" and game not in runningGames:
                runningGames.append(game)
            #if game not running, remove from running games
            if game.get_status() == 'closed':
                runningGames.remove(game)
            #check if total time is greater than timeLimit
            if totalTime > timeLimit and len(runningGames) > 0:
                #send command into queue to kill the tracked game at the given PIDS
                commandQueue.put({"kill" : game.get_pids()})
                #resets the pids of the game and removes it from running games
                if game in runningGames:
                    game.clear_pids()
                    runningGames.remove(game)
        totalTime += timePause
        game.inc_game_runtime(timePause)
        gameNames = [game.get_name() for game in runningGames]
        print("Currently running games %s" % gameNames)
        g.setGameNames(gameNames)
        g.setRunningTime(str(totalTime))

if __name__ == "__main__":
    #TODO terminal only working with first command inputted
    #create a command_interface and a command_executor thread
    interfaceThread = threading.Thread(target=command_interface)
    interfaceThread.start()

    g = GUI()

    trackingLoopThread = threading.Thread(target=runTrackingLoop, args=(g,))
    trackingLoopThread.start()

    
    g.show()
    
