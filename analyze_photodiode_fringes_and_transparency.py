# -*- coding: utf-8 -*-
"""
Created on Tue Nov  3 16:20:00 2020

@author: User
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc
import matplotlib.dates as mdate
import datetime as dt
import os

directory = '/home/vuthalab/Desktop/edm_data/analysis/2021-03-10 - Cooldown, crystal growth, and fringe detection/transparency_runs/'
log_name = '/system_log.txt'
content = os.listdir(directory)

#rc('font',**{'family':'sans-serif','sans-serif':['Libertinus Sans']}) # alternative: 'Linux Biolinum O'
plt.rcParams['font.size'] = 13
plt.rcParams['mathtext.fontset'] = 'cm'     # use Computer Modern for math

Counter = 0
for c in content:
    print(Counter)
    Data = np.loadtxt(directory+c+log_name)
    Times = mdate.date2num(np.array([dt.datetime.fromtimestamp(el) for el in Data[:,0]])) - mdate.date2num(dt.datetime.fromtimestamp(Data[0,0]))
    Reflected = Data[:,3]
    Transmitted = Data[:,4]

    fig, ax = plt.subplots(2,sharex=True)

    ax[0].plot_date(Times,Reflected,'-',lw=2,color='C2',label=c)
    ax[0].set_xlabel("$t$")
    ax[0].set_ylabel("$V$")
    ax[0].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
    ax[0].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
    ax[0].set_ylim([0.0,0.4])
    ax[0].legend(loc='upper right')

    ax[1].plot_date(Times,Transmitted,'-',lw=2,color='C2',label=c)
    ax[1].set_xlabel("$t$")
    ax[1].set_ylabel("$V$")
    ax[1].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
    ax[1].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
    ax[1].set_ylim([0.0,6.0])
    ax[1].legend(loc='upper right')

    # Choose your xtick format string
    date_fmt = '%H:%M:%S'
    # Use a DateFormatter to set the data to the correct format.
    date_formatter = mdate.DateFormatter(date_fmt)
    plt.gca().xaxis.set_major_formatter(date_formatter)
    # Sets the tick labels diagonal so they fit easier.
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()

    Counter += 1





#
# Times_Plot = mdate.date2num(Times)
#
# #Plot pressures
# fig, ax = plt.subplots(nrows=10, sharex=True, figsize=(10,8))
#
# ax[0].plot_date(Times_F10,Voltages_F10,'-',lw=2,color='C2',label='10 sccm')
# ax[0].set_xlabel("$t$")
# ax[0].set_ylabel("$V$")
# ax[0].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[0].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[0].set_ylim([0.0,0.4])
# ax[0].legend(loc='upper right')
#
# ax[1].plot_date(Times_F7,Voltages_F7,'-',lw=2,color='C2',label='7 sccm')
# ax[1].set_xlabel("$t$")
# ax[1].set_ylabel("$V$")
# ax[1].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[1].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[1].set_ylim([0.0,0.4])
# ax[1].legend(loc='upper right')
#
# ax[2].plot_date(Times_F5,Voltages_F5,'-',lw=2,color='C2',label='5 sccm')
# ax[2].set_xlabel("$t$")
# ax[2].set_ylabel("$V$")
# ax[2].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[2].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[2].set_ylim([0.0,0.4])
# ax[2].legend(loc='upper right')
#
# ax[3].plot_date(Times_F2,Voltages_F2,'-',lw=2,color='C2',label='2 sccm')
# ax[3].set_xlabel("$t$")
# ax[3].set_ylabel("$V$")
# ax[3].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[3].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[3].set_ylim([0.0,0.4])
# ax[3].legend(loc='upper right')
#
# ax[4].plot_date(Times_F1,Voltages_F1,'-',lw=2,color='C2',label='1 sccm')
# ax[4].set_xlabel("$t$")
# ax[4].set_ylabel("$V$")
# ax[4].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[4].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[4].set_ylim([0.0,0.4])
# ax[4].legend(loc='upper right')
#
# ax[5].plot_date(Times_B10,Voltages_B10,'-',lw=2,color='C2',label='10 sccm buffer')
# ax[5].set_xlabel("$t$")
# ax[5].set_ylabel("$V$")
# ax[5].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[5].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[5].set_ylim([0.0,0.4])
# ax[5].legend(loc='upper right')
#
# ax[6].plot_date(Times_T6,Voltages_T6,'-',lw=2,color='C2',label='5.6 K')
# ax[6].set_xlabel("$t$")
# ax[6].set_ylabel("$V$")
# ax[6].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[6].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[6].set_ylim([0.0,0.4])
# ax[6].legend(loc='upper right')
#
# ax[7].plot_date(Times_T8,Voltages_T8,'-',lw=2,color='C2',label='8 K')
# ax[7].set_xlabel("$t$")
# ax[7].set_ylabel("$V$")
# ax[7].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[7].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[7].set_ylim([0.0,0.4])
# ax[7].legend(loc='upper right')
#
# ax[8].plot_date(Times_T9,Voltages_T9,'-',lw=2,color='C2',label='9 K')
# ax[8].set_xlabel("$t$")
# ax[8].set_ylabel("$V$")
# ax[8].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[8].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[8].set_ylim([0.0,0.4])
# ax[8].legend(loc='upper right')
#
# ax[9].plot_date(Times_T10,Voltages_T10,'-',lw=2,color='C2',label='10 K')
# ax[9].set_xlabel("$t$")
# ax[9].set_ylabel("$V$")
# ax[9].tick_params(direction='inout', length=4, width=1, colors='k',which='both',labelsize='medium',top='on',right='on')
# ax[9].margins(0,0.05)  # use x_margin=0, choose y_margin appropriately
# ax[9].set_ylim([0.0,0.4])
# ax[9].legend(loc='upper right')
#
#
#
# # Choose your xtick format string
# date_fmt = '%H:%M:%S'
# # Use a DateFormatter to set the data to the correct format.
# date_formatter = mdate.DateFormatter(date_fmt)
# plt.gca().xaxis.set_major_formatter(date_formatter)
# # Sets the tick labels diagonal so they fit easier.
# fig.autofmt_xdate()
# plt.tight_layout()
# plt.show()
#
# #for ext in ["png","pdf","svg"]:
# #    fig.savefig("/home/vuthalab/Desktop/edm_Data/Logging/Pulse_Tube_Test_Nov_28_2020."+ext,format=ext, bbox_inches="tight")
# #plt.show()