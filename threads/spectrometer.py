from headers.oceanfx import OceanFX
from headers.zmq_server_socket import create_server

from headers.edm_util import deconstruct
from headers.util import nom, std


def spectrometer_thread():
    spectrometer = OceanFX()
    with create_server('spectrometer') as publisher:
        while True:
            trans = {}
            rough = {}

            try:
                spectrometer.capture()
            except Exception as e:
                print('Spectrometer capture failed!', e)
                continue

            spectrum = spectrometer.intensities
            (
                I0, roughness,
                beta_0, beta_2, beta_4,
                chisq
            ) = spectrometer.roughness_full

            trans['spec'] = deconstruct(spectrometer.transmission_scalar)
            trans['unexpl'] = deconstruct(I0)

            rough['surf'] = deconstruct(roughness)
            rough['zero-order'] = deconstruct(beta_0)
            rough['second-order'] = deconstruct(beta_2)
            rough['fourth-order'] = deconstruct(beta_4)
            rough['chisq'] = chisq

            data = {
                'wavelengths': list(spectrometer.wavelengths),
                'intensities': {
                    'nom': list(nom(spectrum)),
                    'std': list(std(spectrum)),
                },
                'intercepts': {
                    'nom': list(nom(spectrometer._intercepts)),
                    'std': list(std(spectrometer._intercepts)),
                },
                'fit': {
                    'num-points': list(nom(spectrometer._points)),
                    'chisq-array': list(spectrometer._chisqs),
                    'chisq': deconstruct(spectrometer.chisq),
                },
                'rough': rough,
                'trans': trans,
            }
            publisher.send(data)
