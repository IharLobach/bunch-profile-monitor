import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt


class BunchProfileMonitor:
    def __init__(self, connection_to_scope=None, dt=None):
        """dt in units of ns"""
        self.connection_to_scope = connection_to_scope
        self.dt = dt
        self.v_arr = None
        self.__fourier_transformed_signal = None
        self.__freqs = None
        self.__reconstructed_signal = None
        self.transmission_coefs = None

    @property
    def data_len(self):
        if self.v_arr is None:
            return 0
        else:
            return len(self.v_arr)

    @property
    def fourier_transformed_signal(self):
        return self.__fourier_transformed_signal

    @property
    def fourier_frequencies(self):
        """in units of GHz"""
        return self.__freqs

    @property
    def reconstructed_signal(self):
        return self.__reconstructed_signal

    @property
    def time_arr(self):
        return np.arange(0, self.data_len*self.dt, self.dt)

    def update_data(self):
        """returns True if updated successfully, False otherwise"""
        if self.connection_to_scope is None:
            raise TypeError("connection_to_scope is None")
        else:
            try:
                self.v_arr = self.connection_to_scope.get_waveform()
                return True
            except Exception as e:
                print("Exception in update data for RF probe", e)
                return False

    def perform_fft(self):
        self.__fourier_transformed_signal = np.fft.rfft(self.v_arr)
        self.__freqs = np.fft.rfftfreq(self.data_len, self.dt)
        return self.fourier_transformed_signal, self.fourier_frequencies

    def perform_signal_reconstruction(self):
        self.__reconstructed_signal =\
             np.fft.irfft(self.fourier_transformed_signal
                          / self.transmission_coefs, self.data_len).real
        return self.reconstructed_signal


# legacy code
class TestDataGenerator():
    def __init__(self, cable, dt=0.2, revolution_period=1/0.0075, n_per=10):
        self.cable = cable
        self.dt = dt
        self.revolution_period = revolution_period
        self.n_per = n_per
        self.time_arr = np.arange(0, n_per * self.revolution_period, self.dt)

    def plot_v_arr(self, v_arr, title):
        plt.plot(self.time_arr, v_arr, '-o')
        plt.xlabel("Time, ns")
        plt.ylabel("Voltage, V")
        plt.title(title)
        plt.show()

    def generate_original_gauss_pulses(self, mu=13, sigma=2, n_per=10,
                                       show_plot=False):
        def gauss(sigma_, mu_, x):
            return np.exp(-1.0 / 2.0 / sigma_ / sigma_
                          * np.power((x % self.revolution_period) - mu_, 2))
        v_arr = gauss(sigma, mu, self.time_arr)
        if show_plot:
            self.plot_v_arr(v_arr, "Original Gauss pulses")
        return v_arr

    def generate_attenuated_v_arr_no_noise(self, original_gauss_pulses,
                                           show_plot=False):
        bpm = BunchProfileMonitor(dt=self.dt)
        bpm.v_arr = original_gauss_pulses
        ft, freqs = bpm.perform_fft()
        bpm.transmission_coefs = 1 / self.cable.calc_attenuation(freqs)
        v_arr = bpm.perform_signal_reconstruction()
        if show_plot:
            self.plot_v_arr(v_arr, "Attenuated Gauss pulses, no noise")
        return v_arr

    def randomize_v_arr(self, v_arr, delta, show_plot):
        v_arr = v_arr + np.random.normal(scale=delta, size=len(v_arr))
        if show_plot:
            self.plot_v_arr(v_arr, "Attenuated Gauss pulses plus noise")
        return v_arr
