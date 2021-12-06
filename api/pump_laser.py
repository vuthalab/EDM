import time

from colorama import Fore, Style

from uncertainties import ufloat

from headers.zmq_client_socket import connect_to
from headers.util import display

from headers.rigol_dg4162 import RigolDG4162
from headers.elliptec_rotation_stage import ElliptecRotationStage
from headers.ti_saph import TiSapphire
from headers.filter_wheel import FilterWheel
from headers.wavemeter import WM
from headers.usbtmc import USBTMCDevice

from models.bandpass import target_angle, target_wavelength
from models.polarization import power_and_polarization, eom_gain_from_angle, eom_angle_from_gain


class EOM(RigolDG4162):
    def __init__(self):
        super().__init__()
        self.active_channel = 2
        self.waveform = 'square'
        self.frequency = 20 # Hz
        self.duty_cycle = 50 # %
        self.enabled = True

        self.on()

        # Labjack gain controller
        self._gain_controller = USBTMCDevice(31419, mode='multiplexed', name='EOM Drive Controller')
        self.gain = 2.5

    def on(self):
        self.high = 5
        self.low = 4.95

    def off(self):
        self.low = 0
        self.high = 0.05

    def is_on(self):
        return self.high > 2.5

    @property
    def gain(self):
        n, s = map(float, self._gain_controller.query(f'READ_GENERIC DAC0 3').split())
        return ufloat(n, s)

    @gain.setter
    def gain(self, gain: float):
        assert 0 <= gain <= 5
        self._gain_controller.send_command(f'DAC0 {gain:.4f}')




class MountedBandpass(ElliptecRotationStage):
    @property
    def wavelength(self):
        """Return the center wavelength of the bandpass."""
        return target_wavelength(self.angle)

    @wavelength.setter
    def wavelength(self, target):
        """Set the center wavelength of the bandpass."""
        self.angle = target_angle(target).n


# Selected laser for each wheel position 1-6
WHEEL_DICT = [
    'tisaph',
    None,
    'baf',
    'tisaph',
    'tisaph',
    'tisaph',
]
class PumpLaser:
    def __init__(self):
        self.ti_saph = TiSapphire()
        self.wheel = FilterWheel()
        self.bandpass = MountedBandpass()
        self.wm = WM()
        self.eom = EOM()

        self._monitor = connect_to('scope')
        self._cache = None
        self._target_polarization = 45

    ##### Internal Methods #####
    @property
    def _baf_wavelength(self):
        freq = self.wm.read_frequency(8)
        if freq is None: return 860
        return 299792458/freq

    def _update_cache(self):
        while True:
            _, data = self._monitor.grab_json_data()
            if data is None:
                if self._cache is not None:
                    break
                else:
                    time.sleep(0.5)
            if data is not None and 'ch1' in data:
                v1, v2 = ufloat(*data['ch1']), ufloat(*data['ch2'])
                self._cache = power_and_polarization(v1, v2, self.wavelength)

    def _update_optics(self):
        """Adjust the bandpass and EOM to maintain desired passband and polarization."""
        self.bandpass.wavelength = self.wavelength
        self.polarization = self._target_polarization

    def __str__(self):
        lines = [
            f'{Fore.YELLOW}Source{Style.RESET_ALL}: {self.source}',
            f'{Fore.YELLOW}Wavelength{Style.RESET_ALL}: {self.wavelength} nm',
            f'{Fore.YELLOW}Bandpass Wavelength{Style.RESET_ALL}: {display(self.bandpass.wavelength)} nm',
            f'{Fore.YELLOW}Power{Style.RESET_ALL}: {display(self.power)} mW',
            f'{Fore.YELLOW}Polarization Angle{Style.RESET_ALL}: {display(self.polarization)} degrees',
        ]
        return '\n'.join(lines)

    ##### Public API #####
    @property
    def source(self):
        """Return the current laser source. Will be 'tisaph', 'baf', or None."""
        return WHEEL_DICT[self.wheel.position - 1]

    @source.setter
    def source(self, value):
        """Set the current laser source. Must be 'tisaph', 'baf', or None."""
        self.wheel.position = 1 + WHEEL_DICT.index(value)

        print(f'Setting pump laser source to {Fore.YELLOW}{value}{Style.RESET_ALL}.')

        # Disable tisaph when selecting baf laser
        if value == 'baf': self.ti_saph.verdi.power = 2 

        # Make sure tisaph is lasing when selecting it as source
        if value == 'tisaph' and self.ti_saph.verdi.power < 6:
            self.ti_saph.verdi.power = 6
            time.sleep(2)

        # Adjust bandpass + EOM to match
        if value is not None: self._update_optics()
        time.sleep(2)


    @property
    def wavelength(self):
        """Return the wavelength of the currently selected source."""
        source = self.source
        if source is None: return None
        if source == 'baf': return self._baf_wavelength
        if source == 'tisaph': return self.ti_saph.wavelength

    @wavelength.setter
    def wavelength(self, target):
        """Set the wavelength of the currently selected source."""
        source = self.source
        if source in [None, 'baf']:
            raise ValueError(f'Cannot set the wavelength of laser {source}!')

        # Set wavelength
        self.ti_saph.wavelength = target
        time.sleep(0.5)
        self._update_optics()
        time.sleep(2)


    @property
    def power(self):
        """Return the total pump power in mW."""
        self._update_cache()
        return self._cache[0] + self._cache[1]

    @property
    def polarization(self):
        """Return the polarization angle out of EOM, in degrees."""
        self._update_cache()
        return self._cache[2]

    @polarization.setter
    def polarization(self, angle):
        """Set the polarization angle out of EOM, in degrees."""
        gain = eom_gain_from_angle(angle, self.wavelength).n
        self.eom.gain = max(min(gain, 5), 0)
        self._target_polarization = angle

    @property
    def model_polarization(self):
        """Return the polarization angle out of EOM, in degrees, estimated from the EOM gain and wavelength."""
        return eom_angle_from_gain(self.eom.gain, self.wavelength)
