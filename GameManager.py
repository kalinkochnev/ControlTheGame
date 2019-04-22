import psutil
import datetime
import time
import json
import os

class GameManager():
    def __init__(self, sessionClass, killClass, gameName):
        self.Session = sessionClass
        self.Kill = killClass
        self.trackedGame = gameName
        self.currentlyRunning = []
    
    def watch(self):
        while True:
            self._addCurrentlyRunning()
            self._removeNotRunning()
            time.sleep(10)

    def _checkGameInfo(self, mode):
        if mode == "status":
            for proc in psutil.process_iter() :
                if self.trackedGame == proc.name():
                    return True
            return False

        if mode == "creationTime":
            gamePids = []
            #get pids for the game
            for proc in psutil.process_iter(attrs=['name', 'pid']):
                if proc.info['name'] == self.trackedGame:
                    gamePids.append(proc.info['pids'])
            
            p = psutil.Process()
            lowestTime = int(p.oneshot().create_time(gamePids[0]))
            for pid in gamePids:
                if p.oneshot().create_time(pid) < lowestTime:
                    lowestTime = int(p.oneshot().create_time(pid))
            return lowestTime
        
    def _addCurrentlyRunning(self):
        if _checkGameInfo("status") == True and self.trackedGame not in self.currentlyRunning:
            self.currentlyRunning.append(self.trackedGame)
            gameStartTime = _checkGameInfo("creationTime")
            self.Session.start(gameStartTime)

    def _removeNotRunning(self):
        if _checkGameInfo("status") == False and self.trackedGame in self.currentlyRunning:
            self.currentlyRunning.remove(self.trackedGame)
            self.Session.close()
    
    def userInteract(self):


class Sessions():
    def __init__(self, manageDataClass, gameName):
        self.manageData = manageDataClass
        self.trackedGame = gameName
        
        self.timeToPause = 0
        self.pausesUsed = 0

        self.gameStartTime = 0
        self.gameEndTime = 0
        self.currentDate = datetime.now.strftime("%m/%d/%Y")

    def start(self, timeCreated):
        self.gameStartTime = timeCreated
    def close(self):
        self.gameEndTime = int(time.time())
    def pause(self, timeToPause):
        self.timeToPause += timeToPause
        self.pausesUsed += 1

    def storeData(self):
        jsonText = {
            "gameName":self.trackedGame,
            "times": {
                "startTime":self.gameStartTime,
                "endTime":self.gameEndTime,
                "duration":self.gameEndTime-self.gameStartTime 
            },
            "pausesUsed" : self.pausesUsed,
        }
        self.manageData.storeData(json.dumps(jsonText))
    def loadData(self):

class manageData():
    def __init__(self, jsonData):
        self.jsonData = jsonData
        
    def storeData(self):
        
    def accessDayData(self):
    def accessRangeData(self):


class killGame():
    def __init__(self, gameName):
        self.trackedGame = gameName

    def killGame(self):
        gamePids = []
        #get pids for the game
        for proc in psutil.process_iter(attrs=['name', 'pid']):
            if proc.info['name'] == self.trackedGame:
                gamePids.append(proc.info['pids'])
        
        p = psutil.Process()
        lowestTime = p.oneshot().create_time(gamePids[0])
        for pid in gamePids:
            psutil.Process(pid).kill()

if __name__ == "__main__":
    """
    overwatch = game(1, "Discord")
    
    testOpen = Process(target=overwatch.isGameOpen, args=())
    timer = Process(target=overwatch.timer, args=())
    track = Process(target=overwatch.trackGame, args=())
    
    testOpen.start()
    timer.start()
    track.start()

    overwatch.interactWithUser()

    while True:
        time.sleep(10)
    """