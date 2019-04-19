from datetime import datetime
import time
import psutil

class GameWatcher():
    def __init__(self, timeTracker):
        self.timeTracker = timeTracker
        self.runningGames = {} # one entry per game session {"overatch":Session("foo")}
        self.trackedGames = ["overwatch", "minecraft"]
        self.timeTracker = timeTracker

    def isGameRunning(self, gameName):
        #looks through the list of running sessions and if it find
        if gameName in self.runningGames.keys():
            return True
        else:
            return False

    ''' 
        This is called to start observing the system and recording the games that are running
    ''' 
    def watch(self):
        # get the list of processes on the system
        # if you find running session that no longer has a process currently running
        # then close the session and remove it. 
        while True:
            self._refillSessionsFromRunningProcesses()
            self._cleanUpDeadSessions()
            time.sleep(10) # let is sleep for a bit

    '''
        go through the list of processes, if any of them match the games care about
        create a new session for each game, and record the time the game was started
    '''
    def _refillSessionsFromRunningProcesses(self):
        
        for proc in psutil.process_iter():
            currentTime = datetime.datetime.now().strftime("%H:%M:%S")
            processName = proc.name()
            if processName in self.runningGames and processName in self.trackedGames: 
                self.runningGames[processName] = GameSession(processName, currentTime, self.timeTracker)

    '''
        Go through the list of current game sessions
        and clean up (close) any of them whose process has stopped
    '''           
    def _cleanUpDeadSessions(self):
        for name, session in self.runningGames:
            if self.isProcessRunning(name) == False:
                session.close()
                del self.runningGames[name]

    """
    """
    def isProcessRunning(self, gameName):
        for proc in psutil.process_iter() :
            processName = proc.name()
            if gameName == processName:
                return True
        return False

class GameSession():
    def __init__(self, procName, startTime, timeTracker):
        self.procName = procName
        self.startTime = startTime
        self.timeTracker = timeTracker

    ''' 
    This is how the session is notified that it's ended and it needs to record the time
    ''' 
    def close(self):
        
        timeTracker.recordSession(procName, self.getDuration())
        
    def getDuration(self):
        currentTime = datetime.datetime.now().strftime("%H:%M:%S")
        duration = 
        pass # do some datetime calculation of current time minus start time
        


class TimeTracker():

    '''
        This will record the name of the game and how long the session was 
        in some kind of persistent storage - file, database, whatever
    '''
    def recordSession(self, processName, duration):
        pass # 

'''

'''
class GameLimits():
    pass

if __name__ == 'main': 
    # this is where we will work out the interactions, then we'll make these into test cases

    timeTracker =  TimeTracker()
    gw = GameWatcher(timeTracker)

    gw.watch()

