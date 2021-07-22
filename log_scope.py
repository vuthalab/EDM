import time
from pathlib import Path
import itertools

from colorama import Fore, Style

import numpy as np
import matplotlib.pyplot as plt

from headers.zmq_server_socket import create_server

from headers.rigol_ds1102e import RigolDS1102e

##### Parameters #####
root_dir = Path('~/Desktop/edm_data/logs/scope/').expanduser()
log_file = root_dir / (time.strftime('%Y-%m-%d %H꞉%M꞉%S') + '.txt')

N_AVERAGE = 16 # How many traces to average over

ENABLE_LOGGING = True

if not ENABLE_LOGGING:
    print(f'{Fore.RED}WARNING: LOGGING IS OFF!{Style.RESET_ALL}')
    time.sleep(5)

publisher = create_server('scope')

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
    acquisitions = np.zeros(shape=(2, N_AVERAGE, len(times)))# + photodiode_offset

    # Initialize plot
    plt.ion()

    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    ax1.set_ylabel('Voltage (V)')
    ax2.set_ylabel('Voltage (V)')
    ax2.set_xlabel('Time (s)')

    # Set range
    scope.active_channel=1
    ax1.set_ylim(*scope.voltage_range)
    scope.active_channel=2
    ax2.set_ylim(*scope.voltage_range)

    # Initialize traces
    single1 = ax1.plot(times, acquisitions[0, 0], label='Channel 1')[0]
    average1 = ax1.plot(times, acquisitions[0, 0], label=f'Channel 1 Average (N={N_AVERAGE})')[0]
    single2 = ax2.plot(times, acquisitions[0, 0], label='Channel 2')[0]
    average2 = ax2.plot(times, acquisitions[0, 0], label=f'Channel 2 Average (N={N_AVERAGE})')[0]

    ax1.legend()
    ax2.legend()

    # Begin live plotting
    try:
        with open(log_file, 'a') as f:
            print(scope.time_offset, scope.time_scale, file=f)

            for iteration in itertools.count():
                # Get data
                scope.active_channel = 1
                acq1 = scope.trace
                scope.active_channel = 2
                acq2 = scope.trace

                # Roll acquisition buffer
                acquisitions[:, 1:] = acquisitions[:, :-1]
                acquisitions[0, 0] = acq1
                acquisitions[1, 0] = acq2

                # Plot data occasionally
                if iteration % 4 == 0:
                    single1.set_ydata(acq1)
                    single2.set_ydata(acq2)
                    average1.set_ydata(np.mean(acquisitions[0], axis=0))
                    average2.set_ydata(np.mean(acquisitions[1], axis=0))

                    fig.canvas.draw()
                    fig.canvas.flush_events()

                if ENABLE_LOGGING:
                    print(time.time(), ' '.join(f'{x:.5f}' for x in acq1), file=f)
                    print(time.time(), ' '.join(f'{x:.5f}' for x in acq2), file=f)

                # Log dip sizes
                traces = acquisitions[:, 0]
                dip_size = 100 - 100 * np.min(traces, axis=1) / np.max(traces, axis=1)
                publisher.send({
                    'dip': {
                        'ch1': dip_size[0],
                        'ch2': dip_size[1],
                    }
                })

    except KeyboardInterrupt:
        plt.ioff()
        publisher.close()

