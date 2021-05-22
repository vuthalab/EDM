import datetime
import numpy as np
import math
import os
import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')
import matplotlib.dates as mpdates
from scipy.optimize import curve_fit   # curve_fit is a nonlinear least-squares fit routine
filepath = '/home/vuthalab/Desktop/edm_data/analysis/2021-05-18 - BaF Spectrum 348640-348720 GHz/' #folder with data to analyze
#os.chdir(filepath)
from uncertainties import ufloat
import sys
sys.path.append(filepath)
from util import unweighted_mean, plot, nom, std, fit

## constants 
#Mbaf = 2.61e-25 # mass of BaF in kg 
#c = 2.99e8 #speed of light m/s
#v0= 348658.152 # calculated baf transition we are fitting to
#kb = 1.38e-23 # boltzman constant 

#def fit_func(Freq, a, T ,d):
#    return a*np.exp(- (((Freq-v0)**2)/v0**2)*((Mbaf*c**2)/(2*kb * T))) + d


##### Read Raw Data #####
f_time, freq = np.loadtxt(filepath+'freq-4-5-6-7.txt').T

s_time, traces = [], []
for name in [
   filepath+'scope-4.txt',
   filepath+'scope-5.txt',
   filepath+'scope-6.txt',
]:
    with open(name, 'r') as f:
        time_offset, time_scale = next(f).split()
        for line in f:
            time, *ch1 = line.split()

            _, *ch2 = next(f).split()
            offset = np.mean([float(v) for v in ch2[-200:]])

            # Filter out traces with laser blocked
            if offset < 0.2: continue

            trace = np.array([float(v) for v in ch1])
            trace += offset

            s_time.append(float(time))
            traces.append(np.convolve(trace, np.ones(4)/4)[90:-10])

s_time = np.array(s_time)
traces = np.array(traces)

s_time -= f_time[0]
f_time -= f_time[0]

#print(len(traces))

###### Process Data #####
dip_size = 1 - np.min(traces, axis=1)/np.max(traces, axis=1)
freq_interpolated = np.interp(s_time, f_time, freq)

#plt.imshow(traces - np.max(traces, axis=1)[:, np.newaxis], aspect='auto')
#plt.plot(np.mean(traces, axis=1))
#plt.plot(dip_size)
#plt.plot(freq_interpolated)
#plt.show()

def smooth(arr): return np.convolve(arr, np.ones(10)/10, mode='same')
def smooth_mask(arr): return np.abs(arr - smooth(arr)) < 0.2

mask = (
    smooth_mask(freq_interpolated)
    & smooth_mask(dip_size)
)

x = smooth(freq_interpolated)[mask]
y = 100 * smooth(dip_size)[mask]



#print(len(x))
#print(x[3545])
#print(x[3745])

temps_unc = np.zeros((7,2))
print(temps_unc)
peaks = np.array([[348658.211,0.07],[348673.66,0.07],[348660,1],[0,0],[0,0],[0,0],[0,0]]) #array that contains peak max and eye balled width 

center = peaks[2][0]
width = peaks[2][1]

## constants
Mbaf = 2.61e-25 # mass of BaF in kg
c = 2.99e8 #speed of light m/s
v0= center # calculated baf transition we are fitting to
kb = 1.38e-23 # boltzman constant

def fit_func(Freq, a, T ,d):
    return a*np.exp(- (((Freq-v0)**2)/v0**2)*((Mbaf*c**2)/(2*kb * T))) + d



fit_x = x[(x >= center - width) & (x <= center + width)]
fit_y = y[(x >= center - width) & (x <= center + width)]
print(fit_x.size)
print(fit_y.size)



x_binned = []
y_binned = []

bins = np.linspace(min(fit_x), max(fit_x), len(fit_x))
dx = 0.025 # GHz
#print(dx)

counts = []
for i, x_0 in enumerate(bins):
    # Mask to keep only points within integration window
    mask = abs(fit_x - x_0) < dx/2

    count = np.count_nonzero(mask)
    counts.append(count)

    # Get largest half of values within masked region
    xs = -np.partition(-fit_x[mask], count//2)
    ys = -np.partition(-fit_y[mask], count//2)

    x_binned.append(np.mean(xs))
    y_binned.append(np.mean(ys))
#    print(i, count)


#print(x_binned)

plt.scatter(x_binned,y_binned)
plt.show()

po=[0.5, 40, 0.2]

##fit_params, meta_stuff, residuals = fit(fit_func, fit_x,fit_y, po )
#print(fit_params)

popt, pcov = curve_fit(fit_func, x_binned, y_binned ,p0= po)

a, tau, b = popt


print("Fit parameters",end='\n\n')
for i in range(len(popt)):
    temps_unc[0][0] = popt[1]
    temps_unc[0][1] = pcov[1,1]
    print(f"\t {popt[i]} \t +/- {np.sqrt(pcov[i,i])}")

#print(temps_unc)
new_x = np.linspace(fit_x.min(), fit_x.max(),1000)

fig,ax  = plt.subplots(figsize = (8,6))
ax.set_title('Dopplar Broadening fit aibout 348658.211 GHz BaF: temp 4.1 +/- .6 K ')
ax.set_xlabel("Frequencies (GHz)")
ax.set_ylabel("Intentsty")
ax.plot(x_binned, y_binned, 'o',label ="data")
ax.plot(new_x, fit_func(new_x, *popt),lw = 2, label = "fit")
ax.legend()
plt.tight_layout()
plt.show()
#fig.savefig('dopplar_broaden.png')



#plt.figure(figsize=(48, 8))
#plt.scatter(x, y, s=2)
#plt.xlabel('Frequency (GHz)')
#plt.ylabel('Dip Size (%)')
#plt.locator_params(axis='x', nbins=50)
#plt.show()
#plt.savefig('raw.png', dpi=300)

# Bin Data, average over each bin
#x_binned = []
#y_binned = []

#bins = np.linspace(min(fit_x), max(fit_x), len(fit_x))
#dx = 0.025 # GHz
#print(dx)

#counts = []
#for i, x_0 in enumerate(bins):
    # Mask to keep only points within integration window
#    mask = abs(fit_x - x_0) < dx/2

#    count = np.count_nonzero(mask)
#    counts.append(count)

    # Get largest half of values within masked region
#    xs = -np.partition(-fit_x[mask], count//2)
#    ys = -np.partition(-fit_y[mask], count//2)

#    x_binned.append(unweighted_mean(xs))
#    y_binned.append(unweighted_mean(ys))
#    print(i, count)

#plt.figure(figsize=(48, 8))
#plot(x_binned, y_binned)
#plt.plot(
#    nom(x_binned), nom(y_binned),
#    linewidth=0.5,
#    label=f'Absorption Spectrum (~{np.median(counts):.0f} samples/point)'
#)
#plt.fill_between(
#    nom(x_binned),
#    nom(y_binned) - 2*std(y_binned),
#    nom(y_binned) + 2*std(y_binned),
#    alpha=0.3, label='$2\\sigma$ Confidence Band'
#)
#plt.xlabel('Frequency (GHz)')
#plt.ylabel('Attenuation (%)')
#plt.locator_params(axis='x', nbins=50)

#plt.title('BaF Absorption Spectrum (100% Flashlamp Drive, 4 Hz Ablation, 10 sccm buffer gas)')
#plt.legend()
#plt.tight_layout()
#plt.show()
#plt.savefig('spectrum.png', dpi=300)

##############################################






## Import Frequency Data 


## Import Frequency Data 
#time_freq, freq = np.loadtxt(filepath+'freq-4-5-6-7.txt').T #creates 2 np arrays from frequency spectrum data file (colum1 is time column 2 is freq in Ghz)

#print(time_freq)

#print(freq)

#Import Scope Traces (intensity data)

#time_scope, traces = [], []

#for name in [
#   filepath+'scope-4.txt',
#   filepath+'scope-5.txt',
#   filepath+'scope-6.txt',
#]:
#    with open(name, 'r') as f:
#        time_offset, time_scale = next(f).split()
#        print(time_offset)
#        print(time_scale)
#        for line in f:
   #         time, *ch1 = line.split()

   #         _, *ch2 = next(f).split()
   #         offset = np.mean([float(v) for v in ch2[-200:]])

            # Filter out traces with laser blocked
   #         if offset < 0.2: continue

   #         trace = np.array([float(v) for v in ch1])
   #         trace += offset

   #         s_time.append(float(time))
   #         traces.append(np.convolve(trace, np.ones(4)/4)[90:-10])

#s_time = np.array(s_time)
#traces = np.array(traces)

#s_time -= f_time[0]
#f_time -= f_time[0]





#times = []
#dips = []
#peak_locs = []
#with open(filepath, 'r') as f:
#    time_offset, time_scale = map(float, next(f).split())
#    for line in f:
#        time, *voltages = line.split()
#        time = float(time)
#        voltages = np.array([float(x) for x in voltages])

#       dip = - np.min(voltages)
#        peak_loc = 6*time_scale*(np.argmin(voltages)/len(voltages) - 0.5) + time_offset

#        times.append(time)
#        dips.append(dip)
#        peak_locs.append(peak_loc)


#print(len(times))
#print(len(dips))
#print(len(peak_locs))
#print(len(time_freq))

#print(times[0], times[2200])


##match time of scope with time of frequecy
#freqs = []
#intensity = []

#for i in range(len(time_freq)):
#    for j in range(len(times)):
#        if math.isclose(times[j],time_freq[i][0], rel_tol= 1):
#            freqs.append(time_freq[i][1])
#            intensity.append(dips[j])

#print(len(freqs))
#print(len(intensity))
##plot frequency vs intensity

#plt.plot(freqs,intensity)
#plt.xlabel('frequency (Hz)')
