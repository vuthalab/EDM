import time

import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from uncertainties import unumpy as unp

from headers.oceanfx import OceanFX
from headers.zmq_client_socket import connect_to
from headers.elliptec_rotation_stage import ElliptecRotationStage

from headers.util import uarray, nom, std, plot

NAME = '900nm_test'
input(f'Calibrating filter {NAME}. Press enter to confirm.')


monitor = connect_to('spectrometer')
spec = OceanFX()

mask = (spec.wavelengths > 800) & (spec.wavelengths < 950)
wavelengths = spec.wavelengths[mask]

def get_spectrum():
    while True:
        ts, data = monitor.grab_json_data()
        if data is not None:
            intensities = uarray(data['intensities']['nom'], data['intensities']['std'])
            transmission = (intensities - spec.background)/spec.baseline
            masked = transmission[mask]
            clipped = uarray(
                np.maximum(nom(masked), 1e-8),
                std(masked)
            )
            return -10*unp.log10(clipped)
        time.sleep(0.1)

print('Homing...')
mount = ElliptecRotationStage(offset=-8170)
mount.home()

print('Purging...')
get_spectrum() # Purge spectrum during movement


# DEFINE ANGLE RANGE HERE
#angles = np.linspace(0, 30, 61)
#angles = np.linspace(0, 30, 31)
#angles = np.linspace(0, 40, 9)
#np.random.shuffle(angles)

angles = [-30, 30] # For zeroing calibration


##### Collect data #####
data = []

def make_plot():
    """Save plots of current data."""
    data.sort()

    angles, absorption = zip(*data)
    absorption = np.array(absorption)

    plt.figure(figsize=(8, 6))
    for angle, spectrum in zip(angles, absorption):
        if round(2*angle) % 10 != 0 and len(angles) > 10: continue
#        plot(wavelengths, spectrum, label=f'{angle:.1f}°', clear=False, continuous=True)
        plt.plot(wavelengths, nom(spectrum), label=f'{angle:.1f}°')
    plt.ylabel('Absorption (dB)')
    plt.xlabel('Wavelength (nm)')
    plt.title(f'Absorption vs Wavelength of {NAME.upper()} Filter')
    plt.xlim(min(wavelengths), max(wavelengths))
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'fluorescence/filters/{NAME}.pdf')
    plt.savefig(f'fluorescence/filters/{NAME}.png', dpi=300)
    plt.close()

    plt.figure(figsize=(8, 6))
    plt.imshow(
        nom(absorption)[::-1],
        extent=[min(wavelengths), max(wavelengths), min(angles), max(angles)],
        aspect='auto',
        interpolation='none',
    )
    plt.ylabel('Angle (°)')
    plt.xlabel('Wavelength (nm)')
    plt.title(f'Absorption of {NAME.upper()} Filter')
    cbar = plt.colorbar()
    cbar.ax.set_ylabel('Absorption (dB)')
    plt.tight_layout()
    plt.savefig(f'fluorescence/filters/{NAME}-2d.pdf')
    plt.savefig(f'fluorescence/filters/{NAME}-2d.png', dpi=300)
    plt.close()


with open(f'fluorescence/filters/{NAME}.txt', 'w') as f:
    print('# angle (deg), absorption at each wavelength (dB). First line is wavelengths.', file=f)
    print(9999999999, *wavelengths, file=f)
    for angle in angles:
        print(angle)
        mount.angle = angle

        print('Purging...')
        get_spectrum()

        print('Collecting data...')
        samples = []
        for i in range(1):
            print(f'Sample {i+1}')
            samples.append(get_spectrum())
        absorption = sum(samples) / len(samples)

        data.append((angle, absorption))
        print(angle, *nom(absorption), file=f)
        make_plot()



