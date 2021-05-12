# Setup 24/7 logging
1. Run `multiplexer.py` to create a multiplexer server. This allows multiple programs to use the lab equipment simultaneously.
2. Run `publisher.py` to start the ZMQ publisher. This creates a stream of data logging all sensors in the system.
3. Run `logger.py` to log the ZMQ stream to a file. Logs are stored in `/home/vuthalab/Desktop/edm_data/logs/system_logs`.


# Remotely operating the pulse tube cooler
- start a pyzo shell and run `pulsetube_compressor.py`
- the `pt.keep_logging()` function will print a status report every 2000 s, and also update the long-term pulsetube health log at `/home/vuthalab/Desktop/edm_data/logs/pulsetube/pulsetube_log.txt`
- use `pt.on()` and `pt.off()` to turn the pulsetube on and off. Note that it needs about a minute after being turned off before it can be turned on again.
- normal operating parameters: 
	~90 C lo, 290 C hi near 4 K; higher pressure differential (~250 psi) near room temperature

