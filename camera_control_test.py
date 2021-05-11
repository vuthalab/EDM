# Simple webcam image grab
# import numpy as np
# import cv2
# import matplotlib.pyplot as plt
#
# class Camera:
#     def __init__(self,channel=0):
#         self.capture = cv2.VideoCapture(channel)
#         self.success,self.image = self.capture.read()
#         print("Beginning acquisition ...",)
#
#     def acquire(self):
#         # Acquire image
#         self.success,self.image = self.capture.read()
#         #print ".",
#
#     def close(self):
#         if self.capture.isOpened(): self.capture.release()
#         print("released camera")
#
# camera = Camera()
# camera.capture.set(15,-3)
# camera.capture.set(16,0.01)
# camera.acquire()
# print(camera.image)
# plt.imshow(camera.image)
# plt.show()
# camera.close()

import cv2
import time

vid = cv2.VideoCapture(0)

if vid.isOpened():
    print('Successfully connected')
    while True:
        ret, frame = vid.read()
        print(ret)
        cv2.imshow('frame', frame)
        time.sleep(1)
else:
    print('Failure to connect')

vid.release()

cv2.destroyAllWindows()

"""
Camera parameters:
--------------------
1    CV_CAP_PROP_POS_MSEC Current position of the video file in milliseconds.
2    CV_CAP_PROP_POS_FRAMES 0-based index of the frame to be decoded/captured next.
3    CV_CAP_PROP_POS_AVI_RATIO Relative position of the video file
4    CV_CAP_PROP_FRAME_WIDTH Width of the frames in the video stream.
5    CV_CAP_PROP_FRAME_HEIGHT Height of the frames in the video stream.
6    CV_CAP_PROP_FPS Frame rate.
7    CV_CAP_PROP_FOURCC 4-character code of codec.
8    CV_CAP_PROP_FRAME_COUNT Number of frames in the video file.
9    CV_CAP_PROP_FORMAT Format of the Mat objects returned by retrieve() .
10    CV_CAP_PROP_MODE Backend-specific value indicating the current capture mode.
11    CV_CAP_PROP_BRIGHTNESS Brightness of the image (only for cameras).
12    CV_CAP_PROP_CONTRAST Contrast of the image (only for cameras).
13    CV_CAP_PROP_SATURATION Saturation of the image (only for cameras).
14    CV_CAP_PROP_HUE Hue of the image (only for cameras).
15    CV_CAP_PROP_GAIN Gain of the image (only for cameras).
16    CV_CAP_PROP_EXPOSURE Exposure (only for cameras).
17    CV_CAP_PROP_CONVERT_RGB Boolean flags indicating whether images should be converted to RGB.
18    CV_CAP_PROP_WHITE_BALANCE Currently unsupported
19    CV_CAP_PROP_RECTIFICATION Rectification flag for stereo cameras (note: only supported by DC1394 v 2.x backend currently)
"""
