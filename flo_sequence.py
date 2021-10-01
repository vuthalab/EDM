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
from headers.elliptec_rotation_stage  import ElliptecRotationStage
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
#PMT_GAIN = Labjack(470022275) #LABJACk that sets PMT GAIN
#ONLY PASS 0.5 to 1.1 V. PMT is on DAC0 


#Ti_Saph wavelengths to scan
START_WAVELENGTH = 780 # nm 
END_WAVELENGTH = 830 # nm
WAVELENGTH_SCAN_SPEED = 15 # percentage of maximum
ANGLE = 10 # degrees
DESCRIPTION = f'50hz_BaF_3hours_bg10sccm_2XFELH0850_{ANGLE}Deg_1XFBH0850-40_2XSEMROCK842_Front_15Deg'
INITIAL_GAIN = 1.0

#Verdi Power range
POWER_MIN = 5 #watts
POWER_MAX = 8 #watts
POWER_STEP_SIZE = .1 #watts
NUM_STEPS = int((POWER_MAX - POWER_MIN)/POWER_STEP_SIZE)

#containers for outputs
verdi_power = np.linspace(POWER_MIN, POWER_MAX, num = NUM_STEPS)
LED_voltage = np.zeros(NUM_STEPS)

if SAVE_SEQUENCE is True:
    # Log a copy of this sequence file
    LOG_DIR = Path('~/Desktop/edm_data/logs').expanduser()
    root_dir = LOG_DIR / 'flo_sequences'
    root_dir.mkdir(parents=True, exist_ok=True)
    filename = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.py')

    print('Cloning sequence file to', filename)
    shutil.copy(__file__, filename)



#====== Start Communication with Devices=====#
scope = RigolDS1102e(LABJACK_SCOPE)
verdi = Verdi() # connects to verdi
ti_saph = TiSapphire()
pmt = RigolDP832(RIGOL_PS, 2)
filter_stage = ElliptecRotationStage(offset=-8170)
PMT_GAIN = Labjack(470022275) #LABJACk that sets PMT GAIN ONLY PASS 0.5 to 1.1 V. on DAC
PMT_GAIN.write('DAC0', INITIAL_GAIN) # SETS THE GAIN

#PMT_GAIN IS LOGRITHMIC SEE https://www.hamamatsu.com/resources/pdf/etd/H10720_H10721_TPMO1062E.pdf

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

    filter_stage.angle = ANGLE
    ti_saph.wavelength = START_WAVELENGTH

    pmt.enable()

    while True:       # continuously collect data until manually stoped and/or computer crashes
        try:
            #====Set Up Files ====#
            data_filepath1 ='/home/vuthalab/gdrive/code/edm_control/fluorescence/'+time.strftime('%Y-%m-%d') #make folder for todays runs
            Path(data_filepath1).mkdir(parents = True, exist_ok = True) # if folder doesnt exist, create it
            data_filename1 = DESCRIPTION +'_'+'deg_'+f'{START_WAVELENGTH}'+'nm'+'_'+f'{END_WAVELENGTH}'+'nm '+time.strftime('%Y-%m-%d-%H-%M-%S')+'.txt' #filename for data as txt
            plot_filename = DESCRIPTION +'_'+'deg_'+f'{START_WAVELENGTH}'+'nm'+'_'+f'{END_WAVELENGTH}'+'nm '+time.strftime('%Y-%m-%d-%H-%M-%S')+'.png'  #filename for plot of data
            plot_complete_path = os.path.join(data_filepath1, plot_filename)
            data_complete_path = os.path.join(data_filepath1, data_filename1)
            fi1 = open(data_complete_path,"w")          #create/open data file. if it already exists. it will overwrite
            fi1.write('wavelength(nm)'+'\t'+'flourescence PMT(V)'+'\t'+'ti_saph Power (V)'+'\t'+'Gain (V)'+'\n')  #add header to data file
            #===Take spectroscopy data ===#

            # Initialize containers
            actual_wavelengths = []
            ti_saph_power_pd = []
            FLO_PD = []
            #verdi.power = POWER_MAX # set power for tisaph to max
            # Eat up backlash
            ti_saph.micrometer.speed = 50
            time.sleep(0.5)

            # Set Ti:Saph scanning speed
            ti_saph.micrometer.speed = WAVELENGTH_SCAN_SPEED
            increasing_scan = True
            
            while True:
                GAIN = INITIAL_GAIN
                PMT_GAIN.write('DAC0', GAIN)

                scope.active_channel = 2
                while True:
                    # read voltage on fluorescences detecting photodiode
                    flo_pd_sample = abs(np.average(scope.trace))
                    if abs(flo_pd_sample) < 2.0: break

                    # Decrease gain if saturated
                    GAIN -= 0.1
                    if GAIN < 0.3: break
                    PMT_GAIN.write('DAC0', GAIN)

                # read the voltage on the ti_saph monitoring photodiode
                scope.active_channel = 1
                power_pd_sample = np.average(scope.trace)

                # Get wavelength
                wavelength = ti_saph.wavelength

                print(f'Wavelength: {wavelength:.4f} nm')
                print(f'Ti sapph photodiode reads {power_pd_sample:.4f} V.')
                print(f'Fluorescence photodiode reads {flo_pd_sample:.4f} V.')
                print(f'PMT gain is {GAIN:.3f} V.')
                print()

                if wavelength > START_WAVELENGTH and wavelength < END_WAVELENGTH:
                    # Record values
                    actual_wavelengths.append(wavelength)
                    ti_saph_power_pd.append(power_pd_sample)
                    FLO_PD.append(flo_pd_sample)

                    #save values to data file
                    fi1.write(f'{wavelength}\t{flo_pd_sample}\t{power_pd_sample}\t{GAIN}\n')


                if wavelength > END_WAVELENGTH:
                    # Eat up backlash
                    ti_saph.micrometer.speed = -50
                    time.sleep(0.5)

                    # Flip direction at end of travel
                    ti_saph.micrometer.speed = -WAVELENGTH_SCAN_SPEED
                    increasing_scan = False

                # Stop, record data once we go back to start
                if wavelength < START_WAVELENGTH and not increasing_scan:
                    break

                time.sleep(0.2) 
            
            fi1.close() # close data file
            #====== Calibrate Photodiode ====#

            wavelengths,PD,pwr = import_calibration()   #import calibration data for ti saph power photodiode
            pd_calibration = pwr/PD     #create photodiode calibration (V/W)
            pd_calibration_interpolated = np.interp(actual_wavelengths,wavelengths,pd_calibration)  #interpolate calibration data

            #====Plot calibrated data and save plot ===#
            plt.figure(figsize=(14, 14))
            plt.subplot(3,1,1)
            plt.gca().set_title(f'{START_WAVELENGTH} nm to {END_WAVELENGTH} nm spectrum '+time.strftime('%Y-%m-%d-%h-%M'))
            plt.xlabel('Wavelength (nm)')
            plt.ylabel('Intensity, Normalized')
            plt.yscale('log')
            plt.scatter(actual_wavelengths, FLO_PD/(ti_saph_power_pd*pd_calibration_interpolated), s=2)

            background = 0.95 * np.median(FLO_PD)
            plt.subplot(3,1,2)
            plt.gca().set_title(f'{START_WAVELENGTH} nm to {END_WAVELENGTH} nm spectrum '+time.strftime('%Y-%m-%d-%h-%M'))
            plt.xlabel('Wavelength (nm)')
            plt.ylabel('Background-Subtracted Intensity, Normalized')
            plt.yscale('log')
            plt.scatter(actual_wavelengths, (FLO_PD - background)/(ti_saph_power_pd*pd_calibration_interpolated), s=2)

            plt.subplot(3,1,3)
            plt.gca().set_title('TiSaph Power PD Calibration from'+time.strftime('%Y-%m-%d'))
            plt.xlabel('Wavelength')
            plt.ylabel('Calibration (V/W)')
            plt.scatter(actual_wavelengths, pd_calibration_interpolated, s=2)
            plt.tight_layout()
            plt.savefig(plot_complete_path, dpi=300)
            plt.close()
        except:
            pmt.disable()
            ti_saph.micrometer.off()
            break

