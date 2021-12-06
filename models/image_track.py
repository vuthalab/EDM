import numpy as np
import cv2

from uncertainties import ufloat
from headers.util import unweighted_mean


# For backwards compatibility
def fit_image(image, region_size = 50):
    scale = 255 if isinstance(image[0][0], np.uint8) else 65535

    height, width = image.shape
    total = np.sum(image)

    center_x_estimates = (image @ np.arange(width)) * height/ total
    center_y_estimates = (image.T @ np.arange(height)) * width / total

    center_x = unweighted_mean(center_x_estimates, samples_per_point=width)
    center_y = unweighted_mean(center_y_estimates, samples_per_point=height)

    region = image[
        round(center_y.n-region_size/2) : round(center_y.n+region_size/2),
        round(center_x.n-region_size/2) : round(center_x.n+region_size/2)
    ]
    intensity = region.sum()/scale

    saturation = np.max(image) * 100/scale

    return (100 * center_x/width, 100 * center_y/height, intensity, saturation)





def fit_image_spot(image, region_size = 100):
    scale = 255 if isinstance(image[0][0], np.uint8) else 65535

    # Estimate center of image
    height, width = image.shape

    downsampled_shape = (200, 200)
    resized = cv2.resize(image, downsampled_shape)

    center_y, center_x = np.unravel_index(np.argmax(resized), downsampled_shape)
    center_x *= width/downsampled_shape[1]
    center_y *= height/downsampled_shape[0]

    # Refine estimate using ROI
    try:
        region = image[
            round(center_y-region_size/2) : round(center_y+region_size/2),
            round(center_x-region_size/2) : round(center_x+region_size/2)
        ]
        total = region.sum()
        center_x_estimates = (region @ np.arange(region_size)) * region_size / total
        center_y_estimates = (region.T @ np.arange(region_size)) * region_size / total

        center_x = center_x + unweighted_mean(center_x_estimates, samples_per_point = region_size) - region_size/2
        center_y = center_y + unweighted_mean(center_y_estimates, samples_per_point = region_size) - region_size/2
    except:
        center_x = ufloat(center_x, 10)
        center_y = ufloat(center_y, 10)
        total = image.sum()

    intensity = total / scale
    saturation = np.max(image) * 100/scale
    return (center_x, center_y, intensity, saturation)
