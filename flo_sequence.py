## flo_sequence.py
#code for fluorescene spectoscopy using ti_saph
#Goal: For each new Ti Saph Wavelength. scan ti_saph power vs Fluorescenes LED intensity in order to identify at which wavelengths there is a non linear response

from headers.verdi import Verdi
from headers.ti_saph import TiSapphire
#from headers.oceanfx import OceanFX
from headers.rigol_ds1102e import RigolDS1102e
from headers.edm_util import deconstruct 
from headers.labjack_device import Labjack
from pathlib import Path
from headers.util import plot
from headers.import_calibration import import_calibration
from datetime import datetime
from headers.rigol_dp832 import RigolDP832
import numpy as np 
import time 
import os, shutil
import matplotlib.pyplot as plt
import time 

#=======Define Operating parameters==========#

LABJACK_SCOPE = '/dev/fluorescence_scope' # ADDRESS OF THE OSCILOSCOPE
RIGOL_PS = '/dev/upper_power_supply'
SAVE_SEQUENCE = False
FLOR_SPECTROSCOPY = True

#Ti_Saph wavelengths to scan
START_WAVELENGTH = 750 #nm 
END_WAVELENGTH = 895 #nm
WAVELENGTH_STEP = 1 #nmi
DESCRIPTION = 'Two_Filters_Long_Just_Ne_40micron'
ANGLE = 0 #Deg
NUM_WAVE_STEPS = int((END_WAVELENGTH - START_WAVELENGTH)/WAVELENGTH_STEP)

#Verdi Power range
POWER_MIN = 5 #watts
POWER_MAX = 8 #watts
POWER_STEP_SIZE = .1 #watts
NUM_STEPS = int((POWER_MAX - POWER_MIN)/POWER_STEP_SIZE)

#containers for outputs
verdi_power = np.linspace(POWER_MIN, POWER_MAX, num = NUM_STEPS)
LED_voltage = np.zeros(NUM_STEPS)
target_wavelengths = np.linspace(START_WAVELENGTH, END_WAVELENGTH, NUM_WAVE_STEPS)
actual_wavelengths = np.zeros(NUM_WAVE_STEPS)
ti_saph_power_pd = np.zeros(NUM_WAVE_STEPS)
FLO_PD = np.zeros(NUM_WAVE_STEPS)

if SAVE_SEQUENCE is True:
    # Log a copy of this sequence file
    LOG_DIR = Path('~/Desktop/edm_data/logs').expanduser()
    root_dir = LOG_DIR / 'flo_sequences'
    root_dir.mkdir(parents=True, exist_ok=True)
    filename = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.py')

    print('Cloning sequence file to', filename)
    shutil.copy(__file__, filename)



#====== Start Communication with Devices=====#
#labjack = Labjack('470022275') # Flourescene LED is AIN2, ti_saph power pd is AIN0
scope = RigolDS1102e(LABJACK_SCOPE)
verdi = Verdi() # connects to verdi
ti_saph = TiSapphire()
pmt = RigolDP832(RIGOL_PS, 2)

if False: #code for ramping over Verdi Power 
    Wavelength = round(ti_saph.wavelength, 2) #save current wavelength
    data_filepath = 'fluorescence/'
    data_filename = f'{Wavelength}'+'nm'+time.strftime('%Y-%m-%d-%H-%M-%S')+ '.txt'
    plot_data_filename = f'{Wavelength}'+'nm'+time.strftime('%Y-%m-%d-%H-%M-%S')
    plot_file_complete = f'{data_filepath}'+f'{plot_data_filename}'+'.png'
    complete_path = os.path.join(data_filepath, data_filename)

    fi = open(complete_path ,"w")
    for j in range(NUM_STEPS):
        verdi.power = verdi_power[j]
        scope.active_channel = 1
        LED_voltage[j] = np.average(scope.trace)

        print(LED_voltage[j])
        fi.write(f'{verdi_power[j]}'+'\t'+f'{LED_voltage[j]}'+'\n')
        time.sleep(10/1000)

    fi.close()
    plt.title(f'{Wavelength}nm'+' Power (W) vs Photodiode Response (V) ')
    plt.xlabel('Verdi Power(W)')
    plt.ylabel('PD Response (V)')
    plt.plot(verdi_power,LED_voltage)
    plt.savefig(plot_file_complete)
    plt.show()


if FLOR_SPECTROSCOPY: # code for scaning over different wavelength 
    while True:       # continuously collect data until manually stoped and/or computer crashes
        try:
            #====Set Up Files ====#
            data_filepath1 ='/home/vuthalab/gdrive/code/edm_control/fluorescence/'+time.strftime('%Y-%m-%d') #make folder for todays runs
            Path(data_filepath1).mkdir(parents = True, exist_ok = True) # if folder doesnt exist, create it
            data_filename1 = DESCRIPTION +'_'+f'{ANGLE}'+'deg_'+f'{START_WAVELENGTH}'+'nm'+'_'+f'{END_WAVELENGTH}'+'nm '+time.strftime('%Y-%m-%d-%H-%M-%S')+'.txt' #filename for data as txt
            plot_filename = DESCRIPTION +'_'+f'{ANGLE}'+'deg_'+f'{START_WAVELENGTH}'+'nm'+'_'+f'{END_WAVELENGTH}'+'nm '+time.strftime('%Y-%m-%d-%H-%M-%S')+'.png'  #filename for plot of data
            plot_complete_path = os.path.join(data_filepath1, plot_filename)
            data_complete_path = os.path.join(data_filepath1, data_filename1)
            fi1 = open(data_complete_path,"w")          #create/open data file. if it already exists. it will overwrite
            fi1.write('wavelength(nm)'+'\t'+'flourescence PD(V)'+'\t'+'ti_saph Power (V)'+'\n')  #add header to data file
            #===Take spectroscopy data ===#
            
            for i in range(NUM_WAVE_STEPS):     #scan over wavelengths

                print(round(target_wavelengths[i], 3))
                ti_saph.wavelength = round(target_wavelengths[i], 3)     #change ti_saph wavelength
                
                if i == 0: pmt.enable(); time.sleep(0.5) 
                
                actual_wavelengths[i] = ti_saph.wavelength              # record actual wavelength ti_saph is at
                
                #if i >= 4 and np.abs(actual_wavelengths[i] - actual_wavelengths[i - 4]) < WAVELENGTH_STEP: pmt.disable()
                #if actual_wavelengths[i] > END_WAVELENGTH: pmt.disable()
                scope.active_channel = 1
                ti_saph_power_pd[i] = np.average(scope.trace)  #read the voltage on the ti_saph monitoring photodiode
                
                scope.active_channel = 2
                FLO_PD[i] = np.average(scope.trace)            #read voltage on fluorescences detecting photodiode
                print('Ti sapph photodiode reads ', ti_saph_power_pd[i], 'V.')
                print('Fluorescence photodiode reads ', FLO_PD[i], 'V.\n')

                if np.abs(FLO_PD[i]) > 2.0: 
                    pmt.disable()
                
                fi1.write(f'{actual_wavelengths[i]}'+'\t'+f'{FLO_PD[i]}'+'\t'+f'{ti_saph_power_pd[i]}'+'\n')    #save values to data file
            
            fi1.close() # close data file
            #====== Calibrate Photodiode ====#

            wavelengths,PD,pwr = import_calibration()   #import calibration data for ti saph power photodiode
            pd_calibration = pwr/PD     #create photodiode calibration (V/W)
            pd_calibration_interpolated = np.interp(actual_wavelengths,wavelengths,pd_calibration)  #interpolate calibration data

            #====Plot calibrated data and save plot ===#
            plt.subplot(2,1,1)
            plt.gca().set_title(f'{START_WAVELENGTH}'+'nm '+'to '+f'{END_WAVELENGTH}'+'nm '+'spectrum'+time.strftime('%Y-%m-%d-%h-%M'))
            plt.xlabel('wavelength (nm)')
            plt.ylabel('Intensity normalized')
            plt.scatter(actual_wavelengths, FLO_PD/(ti_saph_power_pd*pd_calibration_interpolated))
            plt.subplot(2,1,2)
            plt.gca().set_title('TiSaph Power PD Calibration from'+time.strftime('%Y-%m-%d'))
            plt.xlabel('Wavelength')
            plt.ylabel('Calibration (V/W)')
            plt.scatter(actual_wavelengths, pd_calibration_interpolated)
          #  plt.show()
            plt.savefig(plot_complete_path)
            plt.close()
    #       plt.show()
        except:
            pmt.disable()
            ti_saph.micrometer.off()
            break


