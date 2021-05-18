import time
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from headers.rigol_ds1102e import RigolDS1102e

##### Parameters #####
root_dir = Path('~/Desktop/edm_data/logs/scope/').expanduser()
log_file = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.txt')

N_AVERAGE = 16 # How many traces to average over

ENABLE_LOGGING = True

##### Main Program #####
# Initialize connection
with RigolDS1102e() as scope:
    # # Set scope 2
    # scope.active_channel = 2
    # scope.voltage_scale = 1 # V/div
    # scope.voltage_offset = -2.5 # V
    #
    # # Set trigger settings
    # scope.trigger_source = 'ch2'
    # scope.trigger_direction = 'rising'
    # scope.trigger_level = 2.5 # V
    # scope.time_scale = 1e-3 # s/div
    # scope.time_offset = 4 * scope.time_scale
    #
    # # Read mean photodiode voltage
    # scope.active_channel = 1
    # scope.voltage_scale = 2.0 # V/div
    # scope.voltage_offset = 0 # V
    # time.sleep(2)
    # photodiode_offset = np.mean(scope.trace)
    #
    # # Set scale + offset of signal trace
    # scope.voltage_scale = 2.0 # V/div
    # scope.voltage_offset = -photodiode_offset
    #
    # # Fine-tune the offset
    # time.sleep(2)
    # photodiode_offset = 0#np.mean(scope.trace)
    # scope.voltage_offset = -photodiode_offset

    # Initialize acquisition buffer
    times = scope.times
    acquisitions = np.zeros(shape=(N_AVERAGE, len(times)))# + photodiode_offset

    # Initialize plot
    plt.ion()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Voltage (V)')
    ax.set_title('Absorption Signal')
    ax.set_ylim(*scope.voltage_range)

    single = ax.plot(times, acquisitions[0], label='Acquisition')[0]
    average = ax.plot(times, acquisitions[0], label=f'Average (N={N_AVERAGE})')[0]
    plt.legend()

    # Begin live plotting
    try:
        with open(log_file, 'a') as f:
            print(scope.time_offset, scope.time_scale, file=f)

            while True:
                acq = scope.trace

                acquisitions[1:] = acquisitions[:-1]
                acquisitions[0] = acq

                single.set_ydata(acq)
                average.set_ydata(np.mean(acquisitions, axis=0))

                fig.canvas.draw()
                fig.canvas.flush_events()

                if ENABLE_LOGGING:
                    print(time.time(), ' '.join(f'{x:.5f}' for x in acq), file=f)

    except KeyboardInterrupt:
        plt.ioff()
