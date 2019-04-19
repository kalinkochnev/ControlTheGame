import time
import os
import psutil
from multiprocessing import Process, Queue, Value
import datetime
import re


class game():
    def __init__(self, time, gameName):
        self.time = time
        self.gameName = gameName

        self.timeElapsedSec = Value('i', 0)
        #self.timeRemaining = 0
        self.timeRemaining = Value('i', 0)
        self.keepTracking = Value('b', True)

        self.additionalTime = 10

        self.Sessions = []
        self.currentSession = 0
        self.currentSessionTime = 0
        self.pausesRemaining = 2

        self.endGame = False
        self.gameOpen = Value('i', 0)

    def timer(self):
        while self.keepTracking.value == True:
            self.timeElapsedSec.value = self.timeElapsedSec.value + 1
            self.timeRemaining.value = self.time*60-self.timeElapsedSec.value
            time.sleep(1)
        self.endGame = True

    def startSession(self): 
        if self.gameOpen.value == 1:
            print("Starting your session...")
            now = datetime.now()
            currentTime = now.datetime.strftime("%H:%M:%S")
            endTime = "N/A"
            game = self.gameName
            self.Sessions.append((self.currentSession, currentTime, endTime, game))
    def endSession(self):
        if self.gameOpen.value == 0:
            (self.currentSession, currentTime, endTime, game) = self.Sessions[self.currentSession]
            endTime = datetime.datetime.strftime("%H:%M:%S")
            self.Sessions[(self.currentSession, currentTime, endTime, game)]
            self.currentSession += 1
            print("process does not exist")

    def interactWithUser(self):
        print("You have played %s minutes so far today" % self.timeElapsedSec.value)
        print("So far %s sessions have been played \n" % self.currentSession)
        print("--------------------------------------------")
        print("Here are the available commands:")
        print("    pause (# of minutes)")
        print("    add time (# < 10)")
        print("    time remaining")
        print("    stop all (WILL STOP GAME!!!)")
        print("--------------------------------------------")
        while True:
            userInput = input()
            splitInput = userInput.lower().split(" ")
            if splitInput[0] == "pause":
                while self.pauseSession(splitInput[1]) == False:
                    self.pauseSession(splitInput[1])
            elif ((splitInput[0] + splitInput[1]) == "addtime"):
                self.addTime(splitInput[2])
            elif ((splitInput[0] + splitInput[1]) == "timeremaining"):
                print("Time remaining: %s" % str(datetime.timedelta(seconds=self.timeRemaining.value)))
            elif (splitInput[0] + splitInput[1]) == "stopall":
                print("Are you sure you want to do this? Y/n")
                confirmInput = input()
                if isinstance(confirmInput.lower(), str) and confirmInput.lower() == "y":
                    print("Stopping all")
                    self.endSession()
                    self.keepTracking = False
                    self.killGame()
                else:
                    continue
                    
            else:
                print("The information you have entered is incorrect, please try again")
    def addTime(self, userInput):
        if int(userInput) > self.additionalTime:
            print("That is more than the alotted time to finish a match")
        elif int(userInput) < 0:
            print("That is not a correct input")
        else:
            print("%s minutes have been added" % int(userInput))
            self.additionalTime = int(userInput)
            self.timeElapsedSec.value -= int(userInput)*60
    def pauseSession(self, input):
        if self.pausesRemaining != 0:
            self.pausesRemaining -= 1
            self.timeElapsedSec.value -= 60*int(input)
            print("Pausing the game for 5 minutes \n %s out of 2 paused used" % self.pausesRemaining)
            return True
        else:
            print("You are out of pauses for the session")
            return False

    def trackGame(self):
        firstLaunch = False
        firstClose = False
        self.isGameOpen()
        while True:
            if self.gameOpen.value == 1 and firstLaunch == False:
                self.currentSessionTime += 1
                self.startSession()
                firstLaunch == True
                firstClose = False
                time.sleep(1)

            if self.endGame == True and firstClose == False:
                self.endSession()
                self.killGame()
                firstClose = True
                firstLaunch = False
                self.keepTracking = False

    def killGame(self):
        for proc in psutil.process_iter():
            if proc.name() == self.gameName:
                proc.kill()
        
        #keep looping to make sure game is still closed
        while True:
            try: 
                for proc in psutil.process_iter():
                    if proc.name() == self.gameName:
                        proc.kill()
                
            except:
                #print("Pids did not exist, continuing")
                pass
            time.sleep(10)

    def preventClose(self):
        #TODO check to see if other python program is running
        #TODO check if other python was edited
        print('something')

    def isGameOpen(self):
        while True:
            for proc in psutil.process_iter(attrs=['pid']):
                if proc.name() == "Discord":
                    print(proc.info)
            #get pids of program
            
            time.sleep(5)    

if __name__ == "__main__":
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


