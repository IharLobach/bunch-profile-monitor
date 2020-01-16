import numpy as np
import matplotlib.pyplot as plt


class BunchProfileMonitor:
    def __init__(self,connection_to_scope=None,dt = None):
        """dt in units of ns"""
        self.connection_to_scope = connection_to_scope
        self.dt = dt
        self.v_arr = None
        self.__fourier_transformed_signal=None
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

    def __update_data_testing(self):
        # with open("C2200pC00000.txt") as f:
        #     lines = f.read().split()
        # data_lines = lines[6:]
        # data_len = len(data_lines)
        # time_arr = []
        # v_arr = []
        # for l in data_lines:
        #     t, v = [float(a) for a in l.split(",")]
        #     time_arr.append(t)
        #     v_arr.append(v)
        # time_arr = [-1.017e-08, -9.9699e-09, -9.7699e-09, -9.5699e-09, -9.3699e-09, -9.1699e-09, -8.9699e-09, -8.7699e-09, -8.5699e-09, -8.3699e-09, -8.1699e-09, -7.9699e-09, -7.7699e-09, -7.5699e-09, -7.3699e-09, -7.1699e-09, -6.9699e-09, -6.7699e-09, -6.5699e-09, -6.3699e-09, -6.1699e-09, -5.9699e-09, -5.7699e-09, -5.5699e-09, -5.3699e-09, -5.1699e-09, -4.9699e-09, -4.7699e-09, -4.5699e-09, -4.3699e-09, -4.1699e-09, -3.9699e-09, -3.7699e-09, -3.5699e-09, -3.3699e-09, -3.1699e-09, -2.9699e-09, -2.7699e-09, -2.5699e-09, -2.3699e-09, -2.1699e-09, -1.9699e-09, -1.7699e-09, -1.5699e-09, -1.3699e-09, -1.1699e-09, -9.6988e-10, -7.6988e-10, -5.6988e-10, -3.6988e-10, -1.6988e-10, 3.0116e-11]
        v_arr = [0.00255744, 0.00191747, 0.00255744, 0.00191747, 0.00191747, 0.00191747, 0.00191747, 0.00255744, 0.00127749, 0.00319742, 0.00191747, 0.00319742, 0.00319742, 0.00191747, 0.00191747, 0.00319742, 0.00255744, 0.00191747, 0.00127749, -2.45751e-06, -0.00256236, -0.00832214, -0.0147219, -0.0262414, -0.039041, -0.0544004, -0.0697598, -0.0780795, -0.0857592, -0.0844792, -0.0799994, -0.0735996, -0.06464, -0.0531204, -0.0435208, -0.0352011, -0.0262414, -0.0217616, -0.0160018, -0.011522, -0.010882, -0.00896211, -0.00576224, -0.00512226, -0.00512226, -0.00576224, -0.00512226, -0.00256236, -0.00384231, -0.00192238, -0.00192238, -0.00320233]
        # time_arr = np.asarray(time_arr)*1e9# ns
        v_arr = np.asarray(v_arr)+np.random.uniform(-0.005,0.005,len(v_arr))# random additive here
        self.v_arr = v_arr
        return self.v_arr

    def update_data(self,testing=False):
        """returns True if updated successfully, False otherwise"""
        if testing:
            self.__update_data_testing()
            return True
        elif self.connection_to_scope is None:
                raise TypeError("connection_to_scope is None")
        else:
            try:
                self.v_arr = self.connection_to_scope.get_waveform()
                return True
            except:
                return False

    def perform_fft(self):
        self.__fourier_transformed_signal = np.fft.rfft(self.v_arr)
        self.__freqs = np.fft.rfftfreq(self.data_len,self.dt)
        return self.fourier_transformed_signal,self.fourier_frequencies

    def perform_signal_reconstruction(self):
        self.__reconstructed_signal = np.fft.irfft(self.fourier_transformed_signal/self.transmission_coefs,self.data_len).real
        return  self.reconstructed_signal



class TestDataGenerator():
    def __init__(self,cable,dt=0.2,revolution_period=1/0.0075,n_per = 10):
        self.cable = cable
        self.dt = dt
        self.revolution_period = revolution_period
        self.n_per = n_per
        self.time_arr = time_arr = np.arange(0, n_per * self.revolution_period, self.dt)

    def plot_v_arr(self,v_arr,title):
        plt.plot(self.time_arr, v_arr, '-o')
        plt.xlabel("Time, ns")
        plt.ylabel("Voltage, V")
        plt.title(title)
        plt.show()


    def generate_original_gauss_pulses(self,mu=13,sigma=2,n_per=10,show_plot=False):
        def gauss(sigma_, mu_, x):
            return np.exp(-1.0 / 2.0 / sigma_ / sigma_ * np.power((x % self.revolution_period) - mu_, 2))
        v_arr = gauss(sigma, mu, self.time_arr)
        if show_plot:
            self.plot_v_arr(v_arr,"Original Gauss pulses")
        return v_arr

    def generate_attenuated_v_arr_no_noise(self,original_gauss_pulses,show_plot=False):
        bpm = BunchProfileMonitor(dt=self.dt)
        bpm.v_arr = original_gauss_pulses
        ft, freqs = bpm.perform_fft()
        bpm.transmission_coefs = 1 / self.cable.calc_attenuation(freqs)
        v_arr = bpm.perform_signal_reconstruction()
        if show_plot:
            self.plot_v_arr(v_arr,"Attenuated Gauss pulses, no noise")
        return v_arr

    def randomize_v_arr(self,v_arr,delta,show_plot):
        v_arr =  v_arr + np.random.normal(scale = delta,size = len(v_arr))
        if show_plot:
            self.plot_v_arr(v_arr,"Attenuated Gauss pulses plus noise")
        return v_arr






