import time
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import itertools

from colorama import Fore, Style

import cv2
import numpy as np
from tensorflow import keras

from headers.util import unweighted_mean


model = keras.models.load_model('models/model.h5', compile=False)

PATTERN_SIZE = np.array([512, 512])
ROI_SIZE = np.array([300, 300])


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

        self._offset = None


    def update(self, frame, exposure):
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
            box = [
                round(center_x - window_width/2),
                round(center_y - window_height/2),
                round(window_width),
                round(window_height),
            ]
            box[0] = max(min(box[0], 1920 - window_width), 0)
            box[1] = max(min(box[1], 1080 - window_height), 0)

            self._offset = np.array([0, 0])
            print('Initializing tracker with bbox', box)
            try:
                self.tracker.init(downsampled, box)
            except:
                print(f'{Fore.RED}TRACKER FAILED TO INIT! Center the beam in the camera.{Style.RESET_ALL}')


        # Crop out bounding box
        x, y = box[:2]
        frame = frame[y:y+box[3], x:x+box[2]]
        
        # Normalize and blur
        frame = cv2.resize(frame, PATTERN_SIZE)/scale
        frame = cv2.GaussianBlur(frame, (81, 81), 0) + 1e-3

        # Normalize to exposure time
        frame *= 5000/exposure

        # Keep a rolling buffer of the last 32 frames.
        self.baseline_buffer.append(frame)
        self.baseline_buffer = self.baseline_buffer[-32:]

        # Compute local baseline.
        baseline = np.mean(self.baseline_buffer, axis=0)

        # Compute fringe pattern
        self.pattern = frame/baseline
        self.n += 1

        # Locate center
        cx, cy = self.roi_center
        w2, h2 = ROI_SIZE//2
        downsized = cv2.resize(
            self.pattern[cy-h2:cy+h2, cx-w2:cx+w2],
            (64, 64)
        ) - 1
        center, log_curvature, has_fringes = model.predict(downsized[np.newaxis, :, :, np.newaxis])
        center = center[0]
        self.has_fringes = has_fringes[0][0] > 0.99

        # Store buffer to smooth out center a bit
        self.center_history.append(center)
        self.center_history = self.center_history[-8:]

        # Get central pixel
        cx, cy = self.center_pixel
        self.reflection = unweighted_mean(self.pattern[cy-5:cy+5, cx-5:cx+5])

        if has_fringes:
            # Shift bounding box if needed
            cx, cy = self.center
            if cx < -0.2: self._offset[0] -= 2
            if cx > 0.2: self._offset[0] += 2
            if cy < -0.2: self._offset[1] -= 2
            if cy > 0.2: self._offset[1] += 2

            # Ensure offset is within bounds.
            bounds = (PATTERN_SIZE - ROI_SIZE)//2
            self._offset[0] = min(max(self._offset[0], -bounds[0]), bounds[1])
            self._offset[1] = min(max(self._offset[1], -bounds[1]), bounds[1])

    @property
    def center(self):
        return np.median(self.center_history, axis=0)

    @property
    def center_pixel(self):
        cx, cy = 0.5 * self.center * ROI_SIZE + self.roi_center
        return (round(cx), round(cy))

    @property
    def roi_center(self):
        return self._offset + PATTERN_SIZE//2

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
        cv2.rectangle(
            pattern,
            self.roi_center - ROI_SIZE//2,
            self.roi_center + ROI_SIZE//2,
            (0, 255, 0),
            1
        )

        return pattern
