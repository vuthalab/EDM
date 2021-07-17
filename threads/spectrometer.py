from headers.oceanfx import OceanFX
from headers.zmq_server_socket import create_server

from headers.edm_util import deconstruct


def spectrometer_thread():
    spectrometer = OceanFX()
    with create_server('spectrometer') as publisher:
        while True:
            trans = {}
            rough = {}

            try:
                spectrometer.capture()
            except:
                print('Spectrometer capture failed!')
                continue

            spectrum = spectrometer.intensities
            (
                I0, roughness,
                fourth_order,
                chisq
            ) = spectrometer.roughness_full

            trans['spec'] = deconstruct(spectrometer.transmission_scalar)
            trans['unexpl'] = deconstruct(I0)

            rough['surf'] = deconstruct(roughness)
            rough['fourth-order'] = deconstruct(fourth_order)
            rough['chisq'] = chisq

            publisher.send({
                'wavelengths': list(spectrometer.wavelengths),
                'intensities': {
                    'nom': list(nom(spectrum)),
                    'std': list(std(spectrum)),
                },
                'intercepts': {
                    'nom': list(nom(spectrometer._intercepts)),
                    'std': list(std(spectrometer._intercepts)),
                },
                'num-points': list(nom(spectrometer._points)),
                'rough': rough,
                'trans': trans,
            })
