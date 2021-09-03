#script to aggreagte different spectroscopy datasets into one
import os
os.chdir('/home/vuthalab/gdrive/code/edm_control/')
#print(os.getcwd())
from headers.import_calibration import import_calibration

import glob 
import numpy as np
import matplotlib.pyplot as plt
import re

CALIBRATION = 'pd_calibration2021-09-02-12-45-36'
CALIBRATION_FILE = CALIBRATION+'.txt'
CALIBRATION_PATH = '/home/vuthalab/gdrive/code/edm_control/fluorescence2021-09-02/'
pathname = '/home/vuthalab/gdrive/code/edm_control/fluorescence/2021-09-03' #folder for which to import data files

#=====import datafiles===#\
start_wavelength = 750
end_wavelength = 830
filter_angle = 0
SELECT_FILES = f'/*{filter_angle}deg_{start_wavelength}nm_{end_wavelength}nm*.txt'
print(pathname+SELECT_FILES)
datafiles = glob.glob(pathname+SELECT_FILES, recursive = True) #import all files with .txt from folder into iterable list

#regexp = re.compile('*(/d)deg*.txt')

#=== Containers for data ===#

Wavelength = np.array([])   #ti_saph wavelength
PD = np.array([])           #fluorescence detection photodiot voltage
PWR = np.array([])          #ti_saph power monitoring photodiode

def import_Spectra(path): #Function for parsing data files
    data = []               #list to contain data
    with open(path) as f:
        print(path)
        next(f)             #skip the header
        for line in f:
            data.append([float(el) for el in line.split()])     #split each line of the file and convert each string in the line into a float
    data1 = np.array(data).T                            #convert our data list into np.array and transpose it
    indices = np.argsort(data1[0])                      #vodoo magic that turns the first column of our 3 column np. array into an index while also sorting the wavelengths (i think it turns the wavelength into a key and the corresponding  flour pd voltage and ti_saph pd voltage are the entry 
    wavel = data1[0][indices]                     #extract the first column as wavelengths while preserving order
    PD = data1[1][indices]                              #extract second column as fluorescene pd voltage while preserving order relative to wavelengths
    pwr = data1[2][indices]                             #extract 3rd column as ti_saph_power pd while presering order relative to wavelengths
    return wavel, PD, pwr
#=====Agregate data from files into our containers ===#

for files in datafiles:
    print(files)
    wavelength1 , pd1, pwr1 = import_Spectra(files)
    Wavelength =  np.concatenate((Wavelength,wavelength1), axis = None) 
    PD =  np.concatenate((PD, pd1), axis = None)
    PWR =  np.concatenate((PWR, pwr1), axis = None)

sorting = np.argsort(Wavelength)
Wavelength = Wavelength[sorting]
PD = PD[sorting]
PWR = PWR[sorting]



#==== Calibrate Ti_saph_power_pd (W/V)
cali_wavelengths, cali_PD, cali_pwr = import_calibration(CALIBRATION_FILE, CALIBRATION_PATH)

#Throw out data below 750nm
PWR = PWR[Wavelength>750]
PD = PD[Wavelength>750]
Wavelength = Wavelength[Wavelength>750]
cali_pwr = cali_pwr[cali_wavelengths>750]
cali_PD = cali_PD[cali_wavelengths>750]
cali_wavelengths = cali_wavelengths[cali_wavelengths>750]

pd_calibration = cali_pwr/cali_PD

#Smooth calibration data
sigma = 4.0
smoothing_wavelengths = np.linspace(np.min(cali_wavelengths),np.max(cali_wavelengths),num=1001)
delta_lambda = smoothing_wavelengths[:,None] - cali_wavelengths
weights = np.exp(-delta_lambda*delta_lambda / (2*sigma*sigma)) / (np.sqrt(2*np.pi) * sigma)
weights /= np.sum(weights, axis=1, keepdims=True)
pd_calibration_smoothed = np.dot(weights, pd_calibration)
pd_calibration_interp = np.interp(Wavelength, smoothing_wavelengths, pd_calibration_smoothed)

#Smooth actual data
sigma = 2.0
#print(np.max(Wavelength))
data_smoothing_wavelengths = np.linspace(np.min(Wavelength),np.max(Wavelength),num=1001)
delta = data_smoothing_wavelengths[:,None] - Wavelength
weights = np.exp(-delta*delta / (2*sigma*sigma)) / (np.sqrt(2*np.pi) * sigma)
weights /= np.sum(weights, axis=1, keepdims=True)
PD_smoothed = np.dot(weights, PD)
PWR_smoothed = np.dot(weights,PWR)
pd_calibration_interp_smoothed = np.interp(data_smoothing_wavelengths,smoothing_wavelengths,pd_calibration_smoothed)

plt.subplot(2,1,1)
plt.gca().set_title( f'TiSaph Power PD Calibration from {CALIBRATION_FILE}')
plt.xlabel('wavelength (nm)')
plt.ylabel('W/V')
plt.plot(cali_wavelengths,pd_calibration,'o',smoothing_wavelengths,pd_calibration_smoothed,'-')
plt.subplot(2,1,2)
plt.gca().set_title(f'Spectrum of Baf in Neon from {SELECT_FILES}')
plt.xlabel('Wavelength (nm)')
plt.ylabel('Intensity')
plt.plot(Wavelength, np.abs(PD/(PWR*pd_calibration_interp)),'o',data_smoothing_wavelengths,np.abs(PD_smoothed/(PWR_smoothed*pd_calibration_interp_smoothed)),'-')
figure = plt.gcf()
plt.savefig(f'{pathname}/{start_wavelength}nm_{end_wavelength}nm_{CALIBRATION}')
plt.show()

