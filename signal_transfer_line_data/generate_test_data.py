import numpy as np
import pandas as pd

from physics_engine.cable_amplifier_transfer_coefs import Amplifier, Cable, \
     SignalTransferLine, HeliaxCableHalfInch


# old test data
# df = pd.read_csv("v_arr_test_0.csv", header=None)
# df.to_csv("v_arr_test.csv")

# new test data
n = 1333
m = 100
dt = 0.1
time = dt*np.arange(m*n)
T = 1/(7.5/1000)

wcm = lambda x: -0.2*np.exp(-((x % T)-60)**2/2/(0.3**2))
file_names = ["TRACE40.CSV", "TRACE41.CSV", "TRACE15.CSV", "TRACE16.CSV",
                  "TRACE20.CSV", "TRACE21.CSV"]
p0, p1, p2, p3, p4, p5 = file_names
amplifier = Amplifier(p0, p1, 0.062, True, True, True)
cable = Cable(p2, p3, p4, p5, 2*0.229952e3, 0.26, True, True, True)
freqs = np.fft.rfftfreq(len(time), dt)
trline = SignalTransferLine([cable, amplifier], freqs)

wcm_res = np.fft.irfft(np.fft.rfft(wcm(time))*trline.transmission_coefs, len(time)).real

rf = lambda x: np.sin(2*np.pi*4/T*x)

pd.Series(wcm_res).to_csv("v_arr_test.csv", index=False)

pd.Series(rf(time)).to_csv("v_rf_arr_test.csv", index=False)
