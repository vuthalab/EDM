import numpy as np
import matplotlib.pyplot as plt

from uncertainties import ufloat

from headers.util import odr_fit, plot, unweighted_mean

data = []
with open('calibration/ti_saph_spec.txt', 'r') as f:
    for line in f:
        spec_n, spec_s, wm_n, wm_s = map(float, line.split())
        spec = ufloat(spec_n, spec_s)
        wm = ufloat(wm_n, wm_s)
        data.append((wm, spec))

wm, spec = np.array(data).T

def model(x, intercept, slope):
    return (x-860) * slope + intercept

p0 = {
    'intercept': (0, 'nm'),
    'slope': (0, ''),
}
params, meta, residuals = odr_fit(model, spec, wm-spec, p0)
print(unweighted_mean(np.abs(residuals)))
plot(spec, wm-spec, model=model, params=params, meta=meta)
plt.show()
