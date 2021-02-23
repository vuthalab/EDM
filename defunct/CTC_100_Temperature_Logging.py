# log temperatures from the SRS CTC 100 temperature controller 

import numpy as np
import os 
import time 
import tkinter as tk 
from tkinter import filedialog as tkFileDialog 

os.chdir("/home/vuthalab/gdrive/code/edm_control/headers")
from CTC100 import CTC100 

#A10771D0

###Useful Functions
 
def getSaveFolder(root_dir): 
    '''
    Create a folder inside folder root_dir to save all recorded data, labelled by the date.    
    Returns the full path to the folder    
    '''
    #Determine the current date for saved data
    day = time.strftime("%d")
    month = time.strftime("%m")
    monthName = time.strftime("%B")
    year = time.strftime("%Y")
    
    #Create save strings
    yearfolder = year + '/'
    monthfolder = month + '_' + monthName + '_' + year + '/'
    dayfolder = monthName + '_' + day + '/'
    timefolder = time.strftime('%H') + '.' + time.strftime('%M') + '.' + time.strftime('%S') + '/'
    
    #Open folder for saving data
    savefolder = root_dir + yearfolder + monthfolder + dayfolder + timefolder
    savefolder = os.path.expanduser(savefolder)
    if not os.path.exists(savefolder):
        #If folder does not already exist, create it    
        os.makedirs(savefolder)    
    return savefolder

###Parameters
 
NitrogenCryostatChannel = 1
HeliumCryostatChannel = 2 
waitTime = 1 #time between datapoints, in seconds
logTimeArray = np.array([30, 0, 0, 0]) #[days, hours, minutes, seconds] 
logTimeSeconds = np.array([24*60**2, 60**2, 60**1, 1]) * logTimeArray 
logTime = np.sum(logTimeSeconds) #total log time in seconds
 
###Initialize Hardware
 
# CTC temp controler
tempcontrol = CTC100("/dev/ttyUSB0") 
print ("CTC100 loaded")
 
###Create Save Folder
 
#Get File Path 
os.chdir("/home/vuthalab/Desktop/edm_data/")
root = tk.Tk().withdraw() 
folder = tkFileDialog.askdirectory(initialdir = os.getcwd()) 
folder = folder + '/'
 
#Set up Save Folders 
saveFolder = getSaveFolder(folder) 
print(saveFolder)
 
## Initialize Runlog and Data Files
 
#Run Log Details
 
description = input("Enter description for this log: ")
 
#Write to Run log
 
logPath = saveFolder + "runlog.txt"
 
mode = 'a' if os.path.exists(logPath) else 'w'
 
with open(logPath, mode) as runlog:
 
    runlog.write('Description: ' + description + "\n")
 
    runlog.write('NitrogenCryostatChannel = ' + str(NitrogenCryostatChannel) +'\n')
 
    runlog.write('HeliumCryostatChannel = ' + str(HeliumCryostatChannel) +'\n')
 
    runlog.write('Estimated Log Time = ' + str(logTime) + ' seconds\n')
 
runlog.close()
 
#Write to Data File
 
dataPath = saveFolder + "data.txt"
 
mode = 'a' if os.path.exists(dataPath) else 'w'
 
dataFile = open(dataPath, mode)
 
if mode == 'w':
 
    header = "#Time[s] \t N2 Temp[K] \t He Temp[K]\n"
 
dataFile.write(header)
 
###Data Acquisition
 
timer = time.time()
print(timer)
 
sCount = timer #1 second counter reference
print(sCount)
tEnd = timer + logTime
print(tEnd)
while (sCount < tEnd):
 
    sCount = time.time() #reset second counter before data acquisition so data transfers while counting
    
    timePoint = time.time()
 
    NitrogenTemp = tempcontrol.read(NitrogenCryostatChannel)
 
    HeliumTemp = tempcontrol.read(HeliumCryostatChannel)
 
    data = str(timePoint) + '\t' + str(NitrogenTemp) + '\t' +'\t' + str(HeliumTemp) + '\n'
    
    dataFile = open(dataPath, 'a')
 
    dataFile.write(data)
 
    dataFile.close()
    
    print("At time ", time.ctime(time.time()))
    print("Channel one temperature is ", NitrogenTemp ) 
    print("Channel two temperature is ", HeliumTemp)
    print('\n')
    time.sleep(waitTime)
print("Log file fully run")
 
