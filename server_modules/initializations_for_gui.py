import os
from physics_engine.bunch_profile_monitor import BunchProfileMonitor
from physics_engine.cable_amplifier_transfer_coefs import Amplifier, Cable, \
     SignalTransferLine, HeliaxCableHalfInch
from server_modules.tcp_communication_with_scope import ConnectionToScope
from server_modules.config_requests import get_from_config
import numpy as np

def init_signal_transfer_line(freqs):
    cwd = os.getcwd()
    file_names = ["TRACE40.CSV", "TRACE41.CSV", "TRACE15.CSV", "TRACE16.CSV",
                  "TRACE20.CSV", "TRACE21.CSV"]
    p0, p1, p2, p3, p4, p5 = [os.path.join(cwd, "bunch-profile-monitor",
                              "signal_transfer_line_data", fn) for fn in
                              file_names]
    amplifier = Amplifier(p0, p1, 0.062, True, True, True)
    cable = Cable(p2, p3, p4, p5, 2*0.229952e3, 0.26, True, True, True)
    return SignalTransferLine([cable, amplifier], freqs)


def init_bpm_signal_transfer_line(conn, plot_dt, data_len):
    bpm = BunchProfileMonitor(connection_to_scope=conn, dt=plot_dt)
    bpm.v_arr = np.zeros(data_len)
    bpm.perform_fft()
    signal_transfer_line = init_signal_transfer_line(bpm.fourier_frequencies)
    bpm.transmission_coefs = signal_transfer_line.transmission_coefs
    bpm.perform_signal_reconstruction()
    return bpm, signal_transfer_line
