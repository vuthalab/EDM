import numpy as np

from uncertainties import ufloat

from headers.util import unweighted_mean, fit

def cone(z):
    return (1 + (1 - np.exp(-4/3 * z))/z) / np.square(1 + z)

def decay_model(r, intensity, width, background):
    z = r/width
    z0 = 20/width
    return intensity * cone(z)/cone(z0) + background
#    return intensity * np.exp(-z) + background
    

p0 = {
    'intensity': (100, 'counts'),
    'width': (20, 'pixels'),
    'background': (500, 'counts'),
}


center = np.array([230, 230])

def fit_cbs(image):
    h, w = image.shape
    x, y = np.meshgrid(np.arange(w), np.arange(h))
    r = np.hypot(x - center[0], y - center[1])

    rs = np.linspace(5, 70, 20)
    dr = np.diff(rs)[0]
    data = []
    for r0 in rs:
        mask = np.abs(r - r0) < dr/2
        samples = image[mask]
        data.append(unweighted_mean(samples))

    try:
        params, meta, residuals = fit(decay_model, rs, data, p0)
        return rs, data, params, meta[1]['chisq/dof']
    except:
        print('CBS fit failed!')
        return rs, data, None, None
