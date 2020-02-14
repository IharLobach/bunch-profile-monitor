import os
from physics_engine.bunch_profile_monitor import BunchProfileMonitor
from physics_engine.cable_amplifier_transfer_coefs import Amplifier, Cable, \
     SignalTransferLine, HeliaxCableHalfInch
from server_modules.tcp_communication_with_scope import ConnectionToScope
from server_modules.config_requests import get_from_config


def init_signal_transfer_line(freqs):
    cwd = os.getcwd()
    file_names = ["TRACE40.CSV", "TRACE41.CSV", "TRACE15.CSV", "TRACE16.CSV",
                  "TRACE20.CSV", "TRACE21.CSV"]
    p0, p1, p2, p3, p4, p5 = [os.path.join(cwd, "bunch-profile-monitor",
                              "signal_transfer_line_data", fn) for fn in
                              file_names]
    amplifier = Amplifier(p0, p1, 2.7, True, True, True)
    cable = Cable(p2, p3, p4, p5, 2*0.229952e3, 0.26, True, True, True)
    return SignalTransferLine([cable, amplifier], freqs)


def init_bpm_signal_transfer_line(useTestData):
    conn = ConnectionToScope()
    dt_ns = get_from_config("dt_ns")
    bpm = BunchProfileMonitor(connection_to_scope=conn, dt=dt_ns)
    attempt = 0
    while True:
        if attempt > 5:
            raise Exception('''Attempted to connect to the scope 5 times.
         No luck.''')
        if bpm.update_data(testing=useTestData):
            break
        attempt += 1
    bpm.perform_fft()
    signal_transfer_line = init_signal_transfer_line(bpm.fourier_frequencies)
    bpm.transmission_coefs = signal_transfer_line.transmission_coefs
    bpm.perform_signal_reconstruction()
    return bpm, signal_transfer_line
