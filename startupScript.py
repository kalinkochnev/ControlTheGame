import os
import json

class SettingsManager():

    def __init__(self):
        #IF THE FILE EVER GETS EDITED AT THIS POINT MODIFY THE CODE THAT ADDS THE DIR PATH INTO THIS FILE TO ADD IT TO THE CORRECT LINE
        #hook for modifying file
        self.settingsDir = ""
        self.settingsDict = {}
    def checkSetup(self):
        print("Checking if all settings are configured correctly...")
        if self.settingsDir == "":
            #gets and checks the directory the user inputted
            print("There was an error with the directory found. It's likely the folder was moved to a different location")
            print("Please input the path of the dir where all the scripts and files are stored \n     ex: /path/to/dir")
            while True:
                directory = str(input())
                if os.path.isdir(os.path.join(directory, "settings.json")):
                    correctInfo = self.fileSetup(directory)
                    if correctInfo == False:
                        continue
                    elif correctInfo == True:
                        break
                else:
                    self.firstTimeSetup()
        else:
            #checks if all correct files are present
            if self.fileSetup(self.settingsDir) == True:
                #checks if the settings file is present, if not it adds the settings for it
                if os.path.isdir(os.path.join(directory, "settings.json")) == False:
                    print("It appears that your settings file is not present, please follow the next steps to configure it.")
                    print("Please be very careful with what you enter because the settings will be EXTREMELY DIFFICULT to change")
                    
                    #sets tracking mode
                    print("Please enter the tracking mode you want: \n     only watch \n     set limits")
                    trackingMode = str(input())
                    self.timeLimitSetting(trackingMode)

                    #sets games to track
                    print("Please enter the names of the games you want to track seperated by spaces \n     ex: Overwatch Destiny Minecraft")
                    gameList = str(input()).split(" ")
                    self.gamesToTrackSettings(gameList)

                    #sets up pausing settings
                    print("Please enter the number of pauses you would like to be allotted followed by the time (in minutes) for each pause seperated by spaces \n     ex: 3 5")
                    print("If you would like no pauses, please input 0 0")
                    while True:
                        pauseInput = str(input()).split(" ")
                        try:
                            pauseInput1 = int(pauseInput[0])
                            pauseInput2 = int(pauseInput[1])
                            if len(pauseInput) != 2:
                                print("That was not a correct input")
                            else:
                                break
                        except ValueError:
                            print("Please make sure you input integers")
                            continue

                    #writes to the json file
                    self.createSettingsFile()
                else:
                    print("All settings are present and correct!")

    def timeLimitSetting(self, timeLimit):
        #for setting limits
        while True:
            if timeLimit == "only watch":
                self.settingsArray["limits"] = "none"
                break
            elif timeLimit == "set limits":
                while True:
                    print("How many minutes should the limit be? \n Make sure this is correct, this CANNOT be changed")
                    try:
                        timeLimit = int(timeLimit())
                        self.settingsArray["limits"] = timeLimit
                        break
                    except ValueError:
                        print("That was not a correct timeLimit, try again")
                        pass
                    except Exception:
                        print("A different exception occurred while converting from an int to a str")
                        pass 
            else:
                print("That was not a correct input, try again")
    def gamesToTrackSettings(self, gameList):
        #for setting what games to track
        formattedList = []
        for game in gameList:
            formattedList.append(game.lower())
        self.settingsDict["games"]= gameList
    def pauseSettings(self, pauseSettings):
        self.settingsArray["numPauses"] = pauseSettings[0]
        self.settingsArray["pauseDuration"] = pauseSettings[1]
    def fileSetup(self, directoryPath):
        while True:
            FileLocationsArray = [directoryPath, os.path.join(directoryPath, "GameManager.py"), os.path.join(directoryPath, "KeepAlive.py") ]
            
            #tests all the dirs
            for directory in FileLocationsArray:
                if os.path.isdir(directory):
                    print("Directory/File Found")
                else:
                    print("Directory/File not found")
                    print("The given directory may not be correct or the following files are not present in the directory\n     GameManager.py\n     KeepAlive.py")
                    return False
            return True

    def firstTimeSetup(self):
        print("Welcome to the game manager! Here is the first time setup")
        print("Please be very careful with what you enter because the settings will be EXTREMELY DIFFICULT to change")
        
        #sets tracking mode
        print("Please enter the tracking mode you want: \n     only watch \n     set limits")
        trackingMode = str(input())
        self.timeLimitSetting(trackingMode)

        #sets games to track
        print("Please enter the names of the games you want to track seperated by spaces \n     ex: Overwatch Destiny Minecraft")
        gameList = str(input()).split(" ")
        self.gamesToTrackSettings(gameList)

        #sets up pausing settings
        print("Please enter the number of pauses you would like to be allotted followed by the time (in minutes) for each pause seperated by spaces \n     ex: 3 5")
        print("If you would like no pauses, please input 0 0")
        while True:
            pauseInput = str(input()).split(" ")
            try:
                pauseInput1 = int(pauseInput[0])
                pauseInput2 = int(pauseInput[1])
                if len(pauseInput) != 2:
                    print("That was not a correct input")
                else:
                    break
            except ValueError:
                print("Please make sure you input integers")
                continue

        #checks if the files are present
        print("Please input the path of the dir where all the scripts and files are stored \n     ex: /path/to/dir")
        while True:
            directory = str(input())
            correctInfo = self.fileSetup(directory)
            if correctInfo == False:
                continue
            if correctInfo == True:
                self.settingsDir = directory
                self.modifyStartupScript()
                break

        #writes to the json
        self.createSettingsFile()
        print("First time setup complete! Please follow the readme in the install folder")
    def createSettingsFile(self):
        settingsLocation = os.path.join(self.settingsDir, "settings.json")
        with open(settingsLocation, "w") as settings:
            jsonData = json.dumps(self.settingsDict, indent=4)
            settings.write(jsonData)
    def modifyStartupScript(self):
        #checks if the dir path is present in the file, adds it if it is not
        scriptDir = os.path.join(self.settingsDir, "startupScript.py")
        with open(scriptDir, 'r') as f:
            lines = f.readlines()
            lineNum = 0
            for line in lines:
                    print(lineNum)
                    if "self.settingsDir = \"\"" in line:
                        print("found")
                        lines[lineNum] = ("        self.settingsDir = \"%s\"\n") % dirToPutIn
                        break
                    lineNum += 1
            with open(scriptDir, 'w') as changeFile:
                for line in lines:
                    print(line)
                    changeFile.write(line)


if __name__ == "__main__":
    startup = SettingsManager()
    startup.checkSetup()