import numpy as np
import matplotlib.pyplot as plt
import time

##read in files
with open('extract.txt', 'r') as file:
    times, freqs, uncert = np.loadtxt(file).T


#local_time = np.ones(times.size)

#for i in range(times.size):
 #  time1= time.localtime(times[i])
 #  print(time1)
   #local_time[i]= time1

#print(times)
#print(local_time)
#print(times1)
print(times.size)
print(freqs)
print(freqs.shape)
#print(freqs1)
plt.plot(times,freqs)
plt.show()