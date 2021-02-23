# logging only pressure 

- start a `pressure publisher` shell in pyzo (autoruns `pressure_gauge_publisher.py`)
- run `pressure_logger.py` to poll the publisher and write into a log file
- log files are stored in `/home/vuthalab/Desktop/edm_data/logs/pressure` in a timestamped folder

# logging pressure & temperature

- start a `pressure publisher` shell in pyzo (autoruns `pressure_gauge_publisher.py`)
- start a `temperature publisher` shell in pyzo (autoruns `thermometer_publisher.py`)
- start a `p+T logger` shell in pyzo (autoruns `pressure_temperature_logger.py`) to poll both publishers and write into a log file
- log files are stored in `/home/vuthalab/Desktop/edm_data/logs/full_system` in a timestamped folder
- use `liveplot_logs.py` to see the logs in real time
- use `examine_logs.py` to plot the logs, zoom in, etc

# remotely operating the pulse tube cooler

- start a pyzo shell and run `pulsetube_compressor.py`
- the `pt.keep_logging()` function will print a status report every 2000 s, and also update the long-term pulsetube health log at `/home/vuthalab/Desktop/edm_data/logs/pulsetube/pulsetube_log.txt`
- use `pt.on()` and `pt.off()` to turn the pulsetube on and off. Note that it needs about a minute after being turned off before it can be turned on again.
- normal operating parameters: 
	~90 C lo, 290 C hi near 4 K; higher pressure differential (~250 psi) near room temperature

