import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from physics_engine.finding_period import get_period
from server_modules.config_requests import get_from_config

iota_freq_MHz = get_from_config("iota_rf_freq_MHz")
h = get_from_config("iota_rf_harmonic")


def sin_fit(x, a, b, frf):
    return a*np.cos(frf*x)+b*np.sin(frf*x)


class RFProbe():
    def __init__(self, probe_to_RF_coef,
                 connection_to_scope=None, dt=None):
        """dt in units of ns"""
        self.connection_to_scope = connection_to_scope
        self.dt = dt
        self.v_arr = None
        self.probe_to_RF_coef = probe_to_RF_coef
        self.rf_freq_GHz = 2*np.pi*h*iota_freq_MHz/1000
    
    @property
    def data_len(self):
        if self.v_arr is None:
            return 0
        else:
            return len(self.v_arr)

    @property
    def time_arr(self):
        return np.arange(0, self.data_len*self.dt, self.dt)

    def update_data(self):
        """returns True if updated successfully, False otherwise"""
        if self.connection_to_scope is None:
            raise TypeError("connection_to_scope is None")
        else:
            try:
                self.v_arr = self.connection_to_scope.get_waveform_RF()
                return True
            except Exception as e:
                print("Exception in update data for RF probe", e)
                return False

    @property
    def rf_voltage_arr(self):
        return self.probe_to_RF_coef*self.v_arr

    def get_amplitude_and_phase(self):
        df0 = pd.DataFrame({'time': self.time_arr,
                            'vol': self.rf_voltage_arr})
        Tiota0 = 2*np.pi*h/self.rf_freq_GHz
        df0 = df0[df0['time'] < Tiota0]
        cos = np.cos(self.rf_freq_GHz*df0['time'])
        sin = np.sin(self.rf_freq_GHz*df0['time'])
        A = np.vstack([cos, sin]).T
        a, b = np.linalg.lstsq(A, df0['vol'], rcond=None)[0]
        c_ampl = a+1j*b
        phase = np.angle(c_ampl, deg=True)
        ampl = np.absolute(c_ampl)
        Tiota = h * get_period(self.rf_voltage_arr, self.dt)
        # print("Tiota = ", Tiota)
        return ampl, phase, Tiota


