import numpy as np
import csv

#path = '/home/vuthalab/gdrive/code/edm_control/headers/'

def import_calibration(filename='pd_calibration.txt', path = '/home/vuthalab/gdrive/code/edm_control/headers/'):
    data = []
    with open(path+filename) as f:
        next(f)
        for line in f:
            data.append([float(el) for el in line.split()])
    data = np.array(data).T
    indices = np.argsort(data[0])
    wavelengths = data[0][indices]
    PD = data[1][indices]
    pwr = data[2][indices]
    return wavelengths, PD, pwr
