import numpy as np

from headers.util import unweighted_mean


def fit_image(image, region_size = 50): # Returns center + intensity (0-1) at center
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
    intensity = unweighted_mean(region.flatten())/scale

    saturation = np.max(image) * 100/scale

    return (100 * center_x/width, 100 * center_y/height, intensity, saturation)
