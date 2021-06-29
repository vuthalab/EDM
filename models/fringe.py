import time

import itertools

from colorama import Fore, Style

import cv2
import numpy as np
from tensorflow import keras

from headers.util import unweighted_mean


model = keras.models.load_model('models/model.h5', compile=False)


# util functions
def find_center(image):
    height, width = image.shape
    center_x = np.sum(image @ np.arange(width)) / image.sum()
    center_y = np.sum(image.T @ np.arange(height)) / image.sum()
    return center_x, center_y

def to_uint8(image):
    return np.clip(255*image, 0, 255).astype(np.uint8)


class FringeModel:
    def __init__(self, window_size=800):
        # factor of sqrt(2) is to compensate for foreshortening
        self.window_size = (window_size/np.sqrt(2), window_size)

        self.tracker = cv2.TrackerMIL_create()
        self.baseline_buffer = []

        self.n = 0
        self.pattern = None

        self.center_history = []
        self.reflection = None
        self.has_fringes = False


    def update(self, frame):
        frame = frame[:, 300:-300]
        scale = 255 if isinstance(frame[0][0], np.uint8) else 65535

        # Try to track pattern.
        downsampled = (255 * frame / scale).astype(np.uint8)
        success = False
        if self.n > 0: (success, box) = self.tracker.update(downsampled)

        if not success:
            # Estimate bounding box manually and init tracker.
            center_x, center_y = find_center(frame)
            window_width, window_height = self.window_size
            box = (
                round(center_x - window_width/2),
                round(center_y - window_height/2),
                round(window_width),
                round(window_height),
            )
            print('Initializing tracker with bbox', box)
            try:
                self.tracker.init(downsampled, box)
            except:
                print(f'{Fore.RED}TRACKER FAILED TO INIT! Center the beam in the camera.{Style.RESET_ALL}')

        # Crop out bounding box
        frame = frame[box[1]:box[1]+box[3], box[0]:box[0]+box[2]]
        
        # Normalize and blur
        frame = cv2.resize(frame, (512, 512))/scale
        frame = cv2.GaussianBlur(frame, (81, 81), 0) + 1e-3

        # Keep a rolling buffer of the last 32 frames.
        self.baseline_buffer.append(frame)
        self.baseline_buffer = self.baseline_buffer[-32:]

        # Compute local baseline.
        baseline = np.mean(self.baseline_buffer, axis=0)

        # Compute fringe pattern
        self.pattern = frame/baseline
        self.n += 1

        # Locate center
        downsized = cv2.resize(self.pattern, (64, 64)) - 1
        center, log_curvature, has_fringes = model.predict(downsized[np.newaxis, :, :, np.newaxis])
        center = center[0]
        self.has_fringes = has_fringes[0][0] > 0.99

        # Store buffer to smooth out center a bit
        self.center_history.append(center)
        self.center_history = self.center_history[-8:]

        # Get central pixel
        cx, cy = self.center_pixel
        self.reflection = unweighted_mean(self.pattern[cy-5:cy+5, cx-5:cx+5])


    @property
    def center_pixel(self):
        center = sum(self.center_history) / len(self.center_history)
        cx, cy = map(round, 0.5 * (center + 1) * np.array(self.pattern.shape[:2]))
        return (cx, cy)

    @property
    def scaled_pattern(self):
        return to_uint8(self.pattern - 0.5)


    @property
    def annotated_pattern(self):
        cx, cy = self.center_pixel
        pattern = cv2.cvtColor(self.scaled_pattern, cv2.COLOR_GRAY2BGR)

        color = 255 if self.has_fringes else 100
        cv2.line(pattern, (cx-10, cy), (cx+10, cy), (0, 0, color), 2)
        cv2.line(pattern, (cx, cy-10), (cx, cy+10), (0, 0, color), 2)
        return pattern
