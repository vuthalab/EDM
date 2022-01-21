import time
import itertools

import cv2

import numpy as np
import matplotlib.pyplot as plt

from uncertainties import ufloat

from simple_pyspin import Camera

from headers.zmq_client_socket import connect_to
from headers.util import plot, uarray

from models.image_track import fit_image_spot
from models.cbs import decay_model


# Select which cameras to show here.
SHOW_CAMERAS = [
#    'webcam', # Micrometer webcam
    'plume', # Ablation Positioning Camera
#    'fringe',
#    'cbs',
]


# Size of region around plume to show
plume_size = 200


print('Initializing cameras...')

if 'cbs' in SHOW_CAMERAS:
    plt.ion()
    fig = plt.figure()

    cbs_socket = connect_to('cbs-camera')


## connect
print('Connecting to publisher...')
if 'plume' in SHOW_CAMERAS: plume_socket = connect_to('plume-cam')
if 'fringe' in SHOW_CAMERAS: fringe_socket = connect_to('fringe-cam')
if 'webcam' in SHOW_CAMERAS: webcam_socket = connect_to('webcam')


def from_png(buff, color=False):
    png = np.frombuffer(buff, dtype=np.uint8)
    return cv2.imdecode(png, int(color))


print('Starting.')
start = time.monotonic()
for i in itertools.count():
    timestamp = f'[{time.monotonic() - start:.3f}]'

    if 'fringe' in SHOW_CAMERAS:
        _, data = fringe_socket.grab_json_data()
        if data is not None:
            frame = from_png(data['png']['raw'])
            pattern = from_png(data['png']['fringe-annotated'], color=True)
            frame = cv2.resize(frame, (720, 540))

            cv2.imshow('Fringe Camera', frame)
            cv2.imshow('Fringe Pattern', pattern)

            print(timestamp, 'fringe')

    if 'cbs' in SHOW_CAMERAS:
        _, data = cbs_socket.grab_json_data()
        if data is not None:
            image = from_png(data['image'], color=cv2.IMREAD_ANYDEPTH).astype(int)
            image = np.maximum(np.minimum((image - 500)//3, 255), 0).astype(np.uint8)
#            image = np.minimum(50 * np.log10(image+1) - 100, 255).astype(np.uint8)
            cv2.imshow('Coherent Backscatter', image)

            print(timestamp, 'cbs')

            # Show CBS fit model
            raw_data = data['data']
            if raw_data is not None:
                r = np.array(raw_data['radius'])
                I = uarray(
                    raw_data['intensity']['nom'],
                    raw_data['intensity']['std'],
                )
                plot(r, I)

                if data['fit'] is not None:
                    r0 = np.linspace(2, 85, 100)
                    model_pred = decay_model(
                        r0,
                        data['fit']['peak'][0],
                        data['fit']['width'][0],
                        data['fit']['background'][0],
                    )
                    plt.plot(r0, model_pred, zorder=-20)

                plt.xlim(2, 85)
                plt.xlabel('Radius (pixels)')
                plt.ylabel('Intensity (counts)')
                plt.title('Coherent Backscatter Fit')
                fig.canvas.draw()

        fig.canvas.flush_events()

    if 'webcam' in SHOW_CAMERAS:
        _, data = webcam_socket.grab_json_data()
        if data is not None:
            frame = from_png(data['raw'], color=True)
            cv2.imshow('Webcam', frame)

            print(timestamp, 'webcam')


    if 'plume' in SHOW_CAMERAS:
        _, data = plume_socket.grab_json_data()
        if data is not None:
            delay = time.time() - data['timestamp']

            frame = from_png(data['png'], color=False)

            cx = ufloat(*data['center']['x'])
            cy = ufloat(*data['center']['y'])
            intensity = data['intensity']
            saturation = data['saturation']
            print(cx, cy, intensity, saturation)

            color = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            annotated = cv2.circle(
                color,
                (round(cx.n), round(cy.n)),
                25, # Radius
                (0, 0, 255), # Color
                2 # Thickness
            )
#            if i % 2 == 0:
            if i % 10 == 0:
                cv2.imshow('Plume', annotated)

            print(timestamp, f'plume {delay:.3f}')


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    time.sleep(2e-2)

cv2.destroyAllWindows()
