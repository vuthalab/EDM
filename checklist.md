Checklist for EDM Experiment
Physical preparations.
1) Install BaF target into buffer gas cell.  Ensure Mylar is properly secured/there is clear optical access to sapphire, BaF target, collimation mirror, etc
2) Ensure sufficient Neon supply
3) Before closing chamber, align 860nm laser through buffer gas cell/ beam path for absorption detection. Once aligned, lock BaF laser to 348.676300 THZ.
        3.1) Optional: align 860nm laser east-west through chamber to probe the ablation plume along its entire path. Note, this will require installing a PD infront of the interferometery optics.
4) Overlap YAG beam with HENE and aim onto target (can be done with chamber open or closed)
        4.1) prior to turning on YAG, ensure the water cooling is on and the turn key is in the on possition
5) Align interferometery optics (i.e. place hene onto sapphire, collect light from back of sapphire onto camera)
6) Align the Tisaph onto the sapphire. Helpful to expand beam and place in center of sapphire.
7) Seal chamber and turn on roughing pump. When chamber is below 0.5 Torr, turbo pump can be activated (use manual.py to do this. Double check that the manual file will only do this by reading it before executing). 
8) once the pressure is stable (around 6.6 E-6 torr is usually the pressure when no leaks are present), perform a leak check with Helium and the RGA to make sure the chamber is properly sealed 
        8.1) if leak check is does not reveal leaks, attach collection optics platform to experiement, otherwise fix leaks.
9) Align fluorescence collection optics:
        9.0) Prior to turning on Tisaph, make sure the water cooling system is on and set to above 20C
        9.1: Depending on wavelength range, install a band passfilter (usually semrock) before tisaph enters chamber to eliminate the tails of the tisaph light
        9.2: Install the necessary long pass filter after chamber before ximea camera (recall that stacked interference filters need at least 1 inch seperation to be effective). Goal of filters is to eliminate light scattered off the Sapphire while allowing fluorescence light through.
        9.3: Document filter configuration sequence_fluorescnce_spectrum.py file in Jason structure 
        9.4 Reduce the background light viewable on the ximea by covering aluminum posts/lens tubes. Recall that aluminum will fluoresce. Also double check the Thorlabs rotation mount's IR led is covered. 


Software preparations: 
10) set up screens for multiplexer, publisher, plotter, and sequence (see operation_procedure.md for instructions) in this order
        10.1 multiplexer runs multiplexer.py, publisher runs publisher.py, plotter runs, liveplot_server.sh, and sequence will run the various growth sequences necessary.

Starting Experiment: 
Cool down:
11) once pressure is about E-6 Torr in the sequence screen run sequence_poweron.py, this will cool the experiment down to 4k 

Grow a neon crystal (no BaF):
12) once system is cold, run sequence_crystal.py to grow a neon crystal
        12.1) double check that the neon bottle is in the open position and that the MFCs are closed prior to running the command
        12.2) edit the sequence file to ensure the desired growth parameters are used.  For the ablation crystal you will run this exact same file again

Collect background fluorescence data on bare neon crystal 
13) run the sequence_fluorescence_spectrum file to collect data on bare neon crystal 

Grow Baf Doped crystal
14) Run the sequence crystal growth file (ensure that the crystal melt sequence is enabled) 
        14.1) while the crystal is growing, ablate BaF using the YAG:
                14.1.1) To ablate, first set the YAG power to 100 and the repetition rate (on the signal generator) to 50Hz
                14.1.2) With the YAG on and the shutter open, gently raster the BaF taget. One should see the ablation plume by eye and ideally will see an absorption dip on both the pd seeing the laser through the buffer gas cell as well as the pd seeing the beam along the entire length of the beam path. 
                14.1.3) stop ablating a few minutes before the neon gas flow stops


Collect Fluorescence data on Baf doped crystal: 
15) run the sequence_flouresence_spectrum.py file. 
        15.1) to analyze the data go to the edm_data\fluorescence\scans folder and run plot. 

To warm up the experiment
16) stop all scans
17) turn off tisaph 
18) run Sequenceoff.py 

