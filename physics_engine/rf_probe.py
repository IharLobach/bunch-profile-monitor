import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os


class RFProbe():
    def __init__(self, probe_to_RF_coef, iota_freq_MHz=7.5,
                 connection_to_scope=None, dt=None):
        """dt in units of ns"""
        self.connection_to_scope = connection_to_scope
        self.dt = dt
        self.v_arr = None
        self.probe_to_RF_coef = probe_to_RF_coef
        self.rf_freq_GHz = 2*np.pi*4*iota_freq_MHz/1000
    
    @property
    def data_len(self):
        if self.v_arr is None:
            return 0
        else:
            return len(self.v_arr)

    @property
    def time_arr(self):
        return np.arange(0, self.data_len*self.dt, self.dt)

    def __update_data_testing(self):
        v_arr_data = pd.read_csv(os.path.join(os.getcwd(),
                                              "bunch-profile-monitor",
                                              "signal_transfer_line_data",
                                              "v_arr_test.csv"), header=None)
        self.v_arr = v_arr_data.values.transpose()[0]
        # random additive here
        time_arr = self.time_arr
        self.v_arr = np.sin(2*np.pi*4/133*time_arr)\
            + np.random.uniform(-0.005, 0.005, len(self.v_arr))
        return self.v_arr

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
        cos = np.cos(self.rf_freq_GHz*self.time_arr)
        sin = np.sin(self.rf_freq_GHz*self.time_arr)
        A = np.vstack([cos, sin]).T
        a, b = np.linalg.lstsq(A, self.rf_voltage_arr, rcond=None)[0]
        c_ampl = a+1j*b
        phase = np.angle(c_ampl, deg=True)
        ampl = np.absolute(c_ampl)
        return ampl, phase
