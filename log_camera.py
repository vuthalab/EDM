from pathlib import Path
from datetime import datetime
import time

from simple_pyspin import Camera

from PIL import Image, ImageFont, ImageDraw

SAVE_INTERVAL = 3/1.4 # seconds. Chosen to match pulsetube frequency
SAVE_DIRECTORY = Path('~/Desktop/edm_data/camera_videos/log').expanduser()

font = ImageFont.truetype('headers/cmunrm.ttf', 24)

with Camera() as cam:
    cam.start()

    while True:
        start = time.monotonic()
        timestamp = datetime.now().strftime('%Y-%m-%d %H꞉%M꞉%S.%f')
        short_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        image = cam.get_array()
        image = Image.fromarray(image)

        draw = ImageDraw.Draw(image)
        draw.text((8, 8), short_timestamp, fill=255, font=font)

        image.save(SAVE_DIRECTORY / f'{timestamp}.png')
        print(timestamp)

        dt = time.monotonic() - start
        time.sleep(max(0, SAVE_INTERVAL - dt))

    cam.stop()
