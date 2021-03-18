#Attempt 1 to create EDM_experiement class
# class to inherit: MFC() from the MFC_Control.py, CTC100() from CTC100_ethernet.py, PulseTube() from pulsetube_compressor.py,
#methods to incorperate: take temperature, take presure liveplot, log data

#TEST COMMENT
import os, sys
sys.path.append('C:/Users/camil/Documents/Github/EDM')
from headers.zmq_server_socket import zmq_server_socket
from headers.zmq_client_socket import zmq_client_socket
from headers.FRG730_ion_gauge_header import FRG730
from headers.CTC100_ethernet import CTC100
from pulsetube_compressor import PulseTube
import os, sys
#sys.path.append("/home/vuthalab/gdrive/code/edm_control")



from MFC_Control import MFC


class EDM(PulseTube, MFC, CTC100, FRG730, zmq_client_socket, zmq_server_socket ): # define a new EDM class that is the child of the existant Pulstube, MFC, CTC100, and FRG730(ion gauge) classes

    def __init__(self):
        PulseTube.__init__(self, address= '192.168.0.101') # initiat pulse tube
        MFC.__init__(self)       #initiate MFC comunication


    def get_temp(self, zmq_client_socket ): #method to get temperature data from pressure temp logger

       #NEED TO MAKE SOCKET CREATION CONDITIONAL ON SOCKET EXISTANCE!!
                #======== Recieve data====#
                connection_settings_CTC100 = {'ip_addr': 'localhost',  # ip address
                    'port': 5551,            # our open port
                    'topic': 'CTC_100'}       # device

                temp_socket= zmq_client_socket(connection_settings_CTC100) # create socket that can recieve information from already running publisher
                temp_socket.make_connection() # connect socket to publisher i.e. let the socket hear what is going on
                #=========Request Temperature Values ====#


                temperatures1 = temp_socket.read_on_demand()[1]['temperatures']

                return temperatures1
    def get_presure(self, zmq_client_socket): #method to get pressure from temp_pressure logger
        #NEED TO MAKE SOCKET CREATION CONDITION ON SOCKET EXISTANCE
        connection_settings_agilent = {'ip_addr': 'localhost',  # ip address
                       'port': 5553,            # our open port
                       'topic': 'FRG730'}       # device
        connection_settings_hornet = {'ip_addr': 'localhost',  # ip address
                        'port': 5550,            # our open port
                        'topic': 'IGM401'}       # device

            agilent_socket = zmq_client_socket(connection_settings_agilent) #create socket to hear agilient presure data
            agilent_socket.make_connection()
            hornet_socket = zmq_client_socket(connection_settings_hornet)#create socket to hear hornet data
            hornet_socket.make_connection()
            #======Request Pressure Values====#
            presure_agilent = agilent_socket.read_on_demand()[1]['pressure']
            presure_hornet = hornet_socket.read_on_demand(1)[1]['pressure']
            #===== Concatanate Pressure Data ====#
            presure_data = presure_agilent + presure_hornet

            return presure_data


    #currently,  The edm class can fully control the MFCs and the pulsetube. NEED TO TEST DATA PRESSURE DATA AND TEMP DATA REQUEST.
    #NEED TO IMPLEMENT LABJACK DATA AQUIZTION




       # CTC100.__init__(self,'192.168.0.104') # ctc100 1
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