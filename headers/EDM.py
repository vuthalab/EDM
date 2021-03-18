#Attempt 1 to create EDM_experiement class
# class to inherit: MFC() from the MFC_Control.py, CTC100() from CTC100_ethernet.py, PulseTube() from pulsetube_compressor.py,
#methods to incorperate: take temperature, take presure liveplot, log data

#TEST COMMENT

from zmq_server_socket import zmq_server_socket
from zmq_client_socket import zmq_client_socket
from FRG730_ion_gauge_header import FRG730
from CTC100_ethernet import CTC100
from pulsetube_compressor import PulseTube
import os, sys
sys.path.append("/home/vuthalab/gdrive/code/edm_control")

#os.chdir('/home/vuthalab/gdrive/code/edm_control/headers')
retval1 = os. getcwd()
print( "current  working directory is %s" %retval1)

os.chdir('/home/vuthalab/gdrive/code/edm_control')
retval = os. getcwd()
print( "current  working directory is %s" %retval)


from MFC_Control import MFC


class EDM(PulseTube, MFC, CTC100, FRG730, zmq_client_socket, zmq_server_socket ): # define a new EDM class that is the child of the existant Pulstube, MFC, CTC100, and FRG730(ion gauge) classes
    def __init__(self):
        PulseTube.__init__(self, address= '192.168.0.101') # initiat pulse tube
        MFC.__init__(self)       #initiate MFC comunication
        CTC100.__init__(self,'192.168.0.104') # ctc100 1
        #CTC100.__init__(self,'192.168.0.107') #ctc100 2
        #connection_settings_CTC100 = {'ip_addr': 'localhost',  # ip address
                    #   'port': 5551,            # our open port
                    #   'topic': 'CTC_100'}       # device
        #connection_settings_agilent = {'ip_addr': 'localhost',  # ip address
         #              'port': 5553,            # our open port
         #              'topic': 'FRG730'}       # device
        #connection_settings_hornet = {'ip_addr': 'localhost',  # ip address
         #              'port': 5550,            # our open port
        #              'topic': 'IGM401'}       # device
        #zmq_client_socket.__init__(self ,connection_settings_CTC100)
        #zmq_client_socket.__init__(self, connection_settings_agilent) # used for data loging
        #self.Agilent_socket.make_connection()
        #zmq_client_socket.__init__(self, connection_settings_hornet) #used for data loging

        #self.CTC100_1_socket.make_connection()
        #zmq_server_socket.__init__(self, port, topic)
       # FRG730.__init__(self, address='/dev/ttyUSB5')  #apparently the FRG730  object is defective


edm = EDM()