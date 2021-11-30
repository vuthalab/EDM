import random
from pathlib import Path

import time
import math
from telnetlib import Telnet

import numpy as np 

from headers.zmq_client_socket import connect_to

from models.mirror_mount import MirrorModel

SONG_DIR = Path('headers/songs/')
songs = [song.stem for song in SONG_DIR.glob('*.txt')]
SECONDS_PER_SIXTEENTH = 1/(1.4 * 8) # tempo, chosen to match pulsetube

DIP_CHANNEL = 'ch1'

# 'Temperature' of the dip optimization algorithm.
# Higher values cause the motion to be more random.
# Lower values cause the algorithm to optimize harder for dip size,
# but increase sensitivity to noise.
TEMPERATURE = 100


Velocity = int
Position = int

NOTES = {
    'C_': 523,
    'C#_': 554,
    'D_': 587,
    'D#_': 622,
    'E_': 659,
    'F_': 698,
    'F#': 740,
    'G': 784,
    'G#': 831,
    'A': 880,
    'A#': 932,
    'B': 988,
    'C': 1047,
    'C#': 1109,
    'D': 1175,
    'D#': 1245,
    'E': 1319,
    'F': 1397,
    'f#': 1480,
    'g': 1568,
    'g#': 1661,
    'a': 1760,
    'a#': 1865,
    'b': 1976,
    'c': 2093,
    'c#': 2217,
    'd': 2349,
}

#defines class for new port model 8742 Picomotor Controller 
class microcontroller:
    """ 
    Class to control newport model 8742 Picomotor Controller 

    Micontroller accepts  stirngs (note that python3+ stores strings as string bytes so b"" is required) that end with \n. multiple commands seperated by ; can be issued simulatenously.
    ex: b'COMAND1;COMMAND2;COMMAND3 \n'
    Commands list can be found https://www.newport.com/medias/sys_master/images/images/h9a/h38/9100236390430/90066734D-8742-Manual.pdf
    """
    def __init__(self, host: str = '192.168.0.100'):
        self.tn = Telnet(host) #initalize handshake with microcontroller

    def _get_int(self, command: str):
        self.tn.write(command.encode())
        time.sleep(10e-3)
        return int(self.tn.read_until(b'\r'))

    def recall(self, val: int) -> None:
        """
        Restores controller working parameters from values saved in nonvolatile memory. passing val = 0 restores factory setting. val = 1 restores last saved settings 
        """
        #format command
        command = '*RCL{}\n'.format(val) #formats command for microcontroller
        
        #send command
        self.tn.write(command.encode()) #sends comand to microcontroller

    
    def reset(self) -> None:
        """
        Soft Reboot of controller cpu. CPU will reload last control parameters in non volatmy. Running this may interupt connection via ethernet 
        """
        #format command 
        command = '*RST\n'
        
        #send command
        self.tn.write(command.encode())


    def abort(self) -> None:
        """"
        Instanteously stops any motion that is occuring 
        """
        # format command
        command = 'AB\n'
        
        #send command
        self.tn.write(command.encode())


    def set_accel(self, motor: int, acc: int):
        """
        set acceleration for a motor (1,2,3,or 4). Motor specifies which motor to control. acc specifies the acceleration to set in steps/second**2. acc rang is 1 to 2000000. The exact step size depends
        on the motor used but usually is less than 30nm.
        """
        #check  input
        if motor>4 or  motor<1:  
            print('Please enter motor value 1,2,3, or 4')
            return
        if acc> 2000000 or acc< 0:
            print('Please enter acc value between 0 and 2000000')
            return


        #format command
        command = '{}AC{};SM\n'.format(motor,acc)

        #send command
        self.tn.write(command.encode())


    def get_accel(self, motor: int) -> int:
        """
        Returns the acceleration of the a given motor. motor can be 1,2,3,or 4.
        Acceleration is returned in units of steps/sec**2
        """
        #check input
        if motor > 4 or motor < 1:
            print('Please enter motor value 1,2,3, or 4')
            return

        #format command
        command = '{}AC?\n'.format(motor)
        
        #send command and get reply as int
       
        accel = self._get_int(command)
        return accel


    def set_home(self, motor, pos):
        """"
        Sets the home position (in terms of steps from neutral) for a given motor. Motor can be 1,2,3,or 4. pos can be between -2147483648 and +2147483647.
        """
        #check input 
        if motor > 4 or motor <1:
            print('Pleae enter motor value 1,2,3, or 4')
            return
        if pos < -2147483648 and pos > 2147483647:
            print('Please enter position value between -2147483648 and +2147483647')
            return

        #format comamand 
        command = f'{motor}DH{pos};SM\n'.encode()

        #send command 
        self.tn.write(command)
        return

    
    def get_home(self, motor):
        """"
        Gets the home position (in terms of steps from neutral) for a given motor. Motor can be 1,2,3,or 4.
        """
        #check input 
        if motor > 4 or motor <1:
            print('Please enter motor value 1,2,3, or 4')
            return

        #format comamand 
        command = f'{motor}DH?\n'

        #send command 
        return self._get_int(command)

    
    def set_motor_type(self):
        """
        Instaneously stops all motor motion, Scans for motors connected to the controller, sets the motor type based on its findings, and saves new settings to memory.
        If the piezo motor is found to be type ‘Tiny’ then velocity (VA) setting is automatically reduced to 1750 if previously set above 1750.
        To accomplish this task, the controllercommands each axis to make a one-step move in the negative directionfollowed by a similar step in the positive direction.
        This process is repeated for all the four axes starting with the first one.  
        """
        #format command
        command = 'AB;MC;SM\n'

        #send command 
        self.tn.write(command.encode())
        return


    def set_motor_type_manual(self, motor, mtype):
        """"
        Manually set the type of motor connected to each motor output on the microcontroller and save to stable memory . Motor corresponds to the output on the microconroller (1,2,3,or 4). 
        mtype is an integer 0,1,2, or 3.
        mtype == 0: no motor connected
        mtype == 1: unknown motor type connected
        mtype == 2: Tiny motor connected. Note tiny motors automatically limit the max velocity to 1750 steps/second
        mtype == 3: standard motor
       """
        #check input
        if motor > 4 or motor < 1:
            print('Please enter motor value 1,2,3, or 4')
            return
        if mtype > 3 or mtype <0:
            print('Please enter mtype  value of 0,1,2,or 3')
            return 

        #format command
        command = '{}QM{};SM\n'.format(motor, mtype)
        
        #send command
        self.tn.write(command.encode())
        return

    def get_motor_type_setting(self,motor):
        """
        Returns what type of motor the microcontroller thinks is connected (does not actually check current motor type). Askings emory for motor type setting. Returns integer of the motor type
        mtype == 0: no motor connected
        mtype == 1: unknown motor type connected
        mtype == 2: Tiny motor connected. Note tiny motors automatically limit the max velocity to 1750 steps/second
        mtype == 3: standard motor
        """
        #check input
        if motor > 4 or motor < 1:
            print('Please enter motor value 1,2,3, or 4')
            return

        #format command
        command = '{}QM?\n'.format(motor)
        
        #send command
        
        #get reply
        mtype= self._get_int(command)
        return mtype



        


    def get_motion(self, motor):
        """
        Determines if specificed motor (1,2,3,4) is moving or not. Returns 1 if motor is moving. Returns 0 if not moving 
        """
        #check input
        if motor > 4 or motor < 1:
            print('Please enter motor value 1,2,3, or 4')
            return

        #format command
        command = '{}MD?\n'.format(motor)
        
        #send command
        
        #get reply
        motion = self._get_int(command)
        return motion

    def get_position(self, motor):
        return self._get_int(f'{motor}TP?\n')

    def get_xy_position(self):
        return (self.get_position(1), self.get_position(2))

    def keep_move(self, motor, dirr):
        """
        Stops current motor motion.Sets specified motor (1,2,3,4) in motion in the specified direction (dirr = + ; or dirr = -). Motor will continue until stop or abort  command is issued
        """

        #check input
        if motor > 4 or motor < 1:
            print('Please enter motor value 1,2,3, or 4')
            return
        if dirr != '+' or dirr !='-':
            print('Please enter dirr value of either + or -')
            return 

        #format command
        command = '{}ST;{}MV{}\n'.format(motor,motor, dirr)
        
        #send command
        self.tn.write(command.encode())
        return

    def move_to(self, motor, pos):
        """
        Stops current motor motion.Starts moving motor to specificed target position. Pos can be -2147483648 and +2147483647. Motor will continue moving unitl target is reached unles stop or aborted
        """
        #check input
        if motor > 4 or motor < 1:    
            print('Please enter motor value 1,2,3, or 4')
            return
        if pos < -2147483648 and pos > 2147483647:
            print('Please enter position value between -2147483648 and +2147483647')
            return



        #format command
        command = '{}ST;{}PA{}\n'.format(motor,motor, pos)
        
        #send command
        self.tn.write(command.encode())
        return


    def where_to(self, motor):
        """
        Determines the specificed motor's (1,2,3,4) target position (in absolute steps relative to neutral 0). Returns positon in steps from 0. 
        """
        #check input
        if motor > 4 or motor < 1:
            print('Please enter motor value 1,2,3, or 4')
            return

        #format command
        command = '{}PA?\n'.format(motor)
        
        #send command
        
        #get reply
        target = self._get_int(command)
        return target


    def move(self, motor, steps):
        """
        Move specificed motor (1,2,3,4) the number of step from where it currently is. steps can accept values within  -2147483648 and +2147483647
        """
        #check input
        if motor > 4 or motor < 1:
            raise ValueError('Please enter motor value 1,2,3, or 4')

        if steps < -2147483648 or steps > +2147483647:
            raise ValueError('Please enter steps value between -2147483648 and +2147483647')

        #format command
        command = '{}PR{}\n'.format(motor, steps)
        
        #send command
        self.tn.write(command.encode())
    

    @property
    def addr(self):
       """
       Gets the controller's current address
       """
       #format command
       command = 'SA?\n'
       
       #send command
       self.tn.write(command.encode())
       #get reply
       time.sleep(10e-3)
       addr = self.tn.read_unti(b'\r')
       return addr


    @addr.setter
    def addr(self, addr):
        """
        Sets the current controller's RS-485 network address. Useful when there are multiple controllers on network that requires unique address. default address = 1. 
        addr can take values between 1 and 31
        """
        #check input
        if addr > 31 or addr < 1:
            print('Please enter addr value between 1 and 31')
            return


        #format command
        command = 'SA{};SM\n'.format(addr)
        
        #send command
        self.tn.write(command.encode())
        return


    def scan_network(self, nn ):
        """
        This command is used to initiate scan of controllers on RS-485 network.  When a master controller receives this command, it scans the RS-485 network for all the slave controllers connected to it.If nn = 0, the master controller scans the network but does not resolve any address conflicts.If nn = 1, the master controller scans the network and resolves address conflicts, if any.  This option preserves the non-conflicting addresses and reassigns the conflicting addresses starting with the lowest available address.  For example, during an initial scan, if the master controller determines that there are unique controllers at addresses 1,2,and 7 and more than one controller at address 23, this option will reassign only the controllers with address conflict at 23; the controllers with addresses 1,2, and 7 will remain untouched.  In this case, after conflict resolution, the final controller addresses might be 1,2,3,7, and 23 if the master determines that there are two (2) controllers initially at address 23.If nn = 2, the master controller reassigns the addresses of all controllers on the network in a sequential order starting with master controller set to address 1.  In the example mentioned above, after reassignment of addresses, the final controller addresses will be 1,2,3,4, and 5.
        """

          #check input
        if nn > 2 or nn < 0:
            print('Please enter nn value 0,1, or 2')
            return



        #format command
        command = 'SC{}\n'.format(nn)
        
        #send command
        self.tn.write(command.encode())
        return

    def get_network_scan(self):
        """
        This command is used to initiate scan of controllers on RS-485 network.  When a master controller receives this command, it scans the RS-485 network for all the slave controllers connected to it.If nn = 0, the master controller scans the network but does not resolve any address conflicts.If nn = 1, the master controller scans the network and resolves address conflicts, if any.  This option preserves the non-conflicting addresses and reassigns the conflicting addresses starting with the lowest available address.  For example, during an initial scan, if the master controller determines that there are unique controllers at addresses 1,2,and 7 and more than one controller at address 23, this option will reassign only the controllers with address conflict at 23; the controllers with addresses 1,2, and 7 will remain untouched.  In this case, after conflict resolution, the final controller addresses might be 1,2,3,7, and 23 if the master determines that there are two (2) controllers initially at address 23.If nn = 2, the master controller reassigns the addresses of all controllers on the network in a sequential order starting with master controller set to address 1.  In the example mentioned above, after reassignment of addresses, the final controller addresses will be 1,2,3,4, and 5.. See https://www.newport.com/medias/sys_master/images/images/h9a/h38/9100236390430/90066734D-8742-Manual.pdf
        page 81 (SC? for more information on meaning of return)
        """
        #format command
        command = 'SC?\n'

        #send command
        self.tn.write(command.encode())
        
        #get reply
        time.sleep(10e-03)  #delay for 10 milliseconds to allow for microcontroller to reply
        scan = self.tn.read_until(b'\r');
        return scan


    def network_scan_status(self):
        """
        Quires about RS-485 network scan status and return 1 if scan is in progress and 0 if scan is not in progress
        """
        #format command
        command = 'SD?\n'
        
        #send command
        #get reply
        return self._get_int(command)
    

    def save_settings(self):
        """
        This command saves the controller settings in its non-volatile memory.The controller restores or reloads these settings to working registers automatically after systemresetor it reboots.  The Purge (XX) commandis used to clear non-volatile memory and restore to factory settings. Note that the SM saves parameters for all motors.  The SM command saves the following settings:1. Hostname(see HOSTNAME command)2. IP Mode(see IPMODE command)3. IP Address(see IPADDRESS command)4. Subnet mask address(see NETMASK command)5. Gateway address(see GATEWAY command)6. Configuration register(see ZZ command)7. Motor type(see QM command)8. Desired Velocity(see VA command)9. DesiredAcceleration(see AC command)
        """
        #format command
        command = 'SM\n'
        
        #send command
        self.tn.write(command.encode())


    def stop_move(self, motor: int) -> None:
        """
        Stops the motion of a motor (1,2,3,4)
        """
        #check input
        if motor > 4 or motor < 1:
            raise ValueError('Please enter motor value 1, 2, 3, or 4')

        #format command
        command = '{}ST?\n'.format(motor)
        
        #send command
        self.tn.write(command.encode())

    
    def set_speed(self, motor: int, vel: int) -> None:
        """
        Set and save new speed for chosen motor (1, 2, 3, or 4). speed can be between 1 and 2000
        """
        #check input
        if motor > 4 or motor < 1:
            raise ValueError('Please enter motor value 1, 2, 3, or 4')

        if vel > 2000 or vel < 1:
            raise ValueError('Please enter vel value between 1 and 2000')

        #format command
        command = '{}VA{};SM\n'.format(motor, vel)
        
        #send command
        self.tn.write(command.encode())

    
    def get_speed(self, motor):
        """
        Determines speed of specificed motor (1,2,3,4) 
        """
        #check input
        if motor > 4 or motor < 1:
            print('Please enter motor value 1,2,3, or 4')
            return

        #format command
        command = '{}VA?\n'.format(motor)
        
        #send command      
        #get reply
        return self._get_int(command) 

    @property
    def firmware_version(self):
        """
        Get the firmware version of the microcontroller
        """
         #format command
        command = 'VE?\n'
        
        #send command
        self.tn.write(command.encode())
        
        #get reply
        time.sleep(10/1000)  #delay for 10 milliseconds to allow for microcontroller to reply
        ver = self.tn.read_until(b'\r')
        return ver.decode()


    def purge_memory(self) -> None:
        """
        Removes all user settings from memory and returns to factory default settings 
        """
        #format command
        command = 'XX\n'
        
        #send command
        self.tn.write(command.encode())




    @property
    def register_config(self) -> str:
        """
        Get current register configuration. See page 89 of manuel for understanding output 
         https://www.newport.com/medias/sys_master/images/images/h9a/h38/9100236390430/90066734D-8742-Manual.pdf

        """
         #format command
        command = b'ZZ?\n'
        
        #send command
        self.tn.write(command)
        
        #get reply
        time.sleep(10e-3)  #delay for 10 milliseconds to allow for microcontroller to reply
        reg  = self.tn.read_until(b'\r');
        return reg.decode()


    @register_config.setter
    def register_config(self, nn: str) -> None:
        """
        Configures and saves the regiaster setting for the microcontroller. 
        See page 89 of the user manuel for input intructions for nn 
        https://www.newport.com/medias/sys_master/images/images/h9a/h38/9100236390430/90066734D-8742-Manual.pdf
        """
        #format command
        command = 'ZZ{}\n'.format(nn)
        
        #send command
        self.tn.write(command.encode())


    @property
    def ip_addr(self) -> str:
        """
        returns microscontroller's current ip address
        """
        #format command
        command = b'IPADDR?\n'
        
        #send command
        self.tn.write(command)
        
        #get reply
        time.sleep(10e-3)  #delay for 10 milliseconds to allow for microcontroller to reply
        addr  = self.tn.read_until(b'\r');
        return addr.decode()

    
    @property
    def is_dhcp(self) -> bool:
        """
        Obtains microcontroller's current ip mode. Return 0 means it has static IP address. Return 1 means it is using DHCP mode.
        """
        #format command
        command = 'IPMODE?\n'
        
        #send command
        #get reply
        return bool(self._get_int(command))

     
    @property
    def mac_addr(self):
        """
        Obtains microcontroller MAC addres
        """
        #format command
        command = b'MACADDR?\n'
        
        #send command
        self.tn.write(command)
        
        #get reply
        time.sleep(10e-3)  #delay for 10 milliseconds to allow for microcontroller to reply
        mac  = self.tn.read_until(b'\r')
        return mac.decode()
    

    @property
    def netmask(self) -> str:
        """
        Obtains microcontroller's current network mask
        """
        #format command
        command = b'NETMASK?\n'
        
        #send command
        self.tn.write(command)
        
        #get reply
        time.sleep(10/1000)  #delay for 10 milliseconds to allow for microcontroller to reply
        mask  = self.tn.read_until(b'\r');
        return mask.decode()

    
    @property
    def hostname(self) -> str:
        """
        Obtains microcontroller's current host name
        """
        #format command
        command = b'HOSTNAME?\n'
        
        #send command
        self.tn.write(command)
        
        #get reply
        time.sleep(10/1000)  #delay for 10 milliseconds to allow for microcontroller to reply
        hostname = self.tn.read_until(b'\r');
        return hostname.decode()


    ##### Fancy functions #####
    def move_with_speed(self, motor: int, pos: Position, vel: Velocity) -> None:
        self.set_speed(motor, vel)
        self.move_to(motor, pos)

    def home(self):
        print('Homing 1')
        self.move_with_speed(1, 0, 2000)
        while abs(self.get_position(1)) != 0:
            print(self.get_position(1))
            time.sleep(0.3)

        print('Homing 2')
        self.move_with_speed(2, 0, 2000)
        while abs(self.get_position(2)) != 0:
            print(self.get_position(2))
            time.sleep(0.3)


    @property
    def _dip_size(self):
        samples = []
        while True:
            ret = self.client_socket.grab_data()
            if ret is None: break

            ts, data = self.client_socket._decode(ret)
            samples.append(data['dip'][DIP_CHANNEL])

        if len(samples) > 0:
            return 10 * np.log(np.mean(samples))
        else:
            return None


    def play_song(self, name: str, amplitude=1):
        pos = np.array(self.get_xy_position(), dtype=int)
        last = (
            np.array(pos, dtype=int),
            self._dip_size
        )

        print(f'Playing {name}')
        song = SONG_DIR / f'{name}.txt'

        # Absolute time for accuracy
        start = time.monotonic()
        beats = 0
        with song.open('r') as f:
            transpose = float(next(f)) * 0.7

            for i, entry in enumerate(f):
                entry = entry.strip()
                if not entry or entry.startswith('#'): continue

                note, duration = entry.split()
                duration = float(duration)
                beats += duration

                # Alternate motors and directions
#                motor = i % 2
#                sign = 1 if (i//2) % 2 == 0 else -1

                # Go in direction of maximum gradient
                gradient = np.array(self.model.gradient) * 6e4/TEMPERATURE
                motor = i % 2
                threshold = np.arctan(gradient[motor]) * 2/np.pi
                sign = 1 if np.random.uniform(-1, 1) < threshold else -1

                if note != 'X':
                    freq = round(NOTES[note] * transpose) * amplitude 
                    steps = round(0.4 * duration * SECONDS_PER_SIXTEENTH * freq)

                    pos[motor] += steps * sign
                    self.move_with_speed(motor + 1, pos[motor], freq)

                # Log position
                if np.hypot(*(pos - last[0])) > 200:
                    real_pos = np.array(self.get_xy_position(), dtype=int)
                    curr_dip = self._dip_size

                    if curr_dip is not None:
                        delta_pos = real_pos - last[0]
                        delta_dip = curr_dip - last[1]
                        self.model.update(*delta_pos, delta_dip)

                        print(
                            'Position:', real_pos,
                            '|',
                            'Dip Size', curr_dip,
                            '|',
                            'Gradient:', gradient,
                        )
                        print(delta_pos, delta_dip)
                        last = (np.array(real_pos, dtype=int), curr_dip)

                end = start + beats * SECONDS_PER_SIXTEENTH
                time.sleep(max(0, end - time.monotonic()))

            # End on integer measure
            song_end = 16 * math.ceil(beats/16)
            end = start + song_end * SECONDS_PER_SIXTEENTH
            time.sleep(max(0, end - time.monotonic()))


    def music_scan(self, amplitude=1):
        self.client_socket = connect_to('scope')
        self.client_socket.make_connection()
        self.model = MirrorModel()

        input('Press enter once on pulse tube beat')

        while True:
            random.shuffle(songs)
            for song in songs:
                self.play_song(song, amplitude=amplitude)

                # Sleep for one measure
                time.sleep(SECONDS_PER_SIXTEENTH * 16)
