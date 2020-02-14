import pandas as pd
import numpy as np


class TransmissionElement():
    def __init__(self, extrapolate_left=False, extrapolate_right=False):
        self.freqs0 = [None]
        self.transmission_coefs0 = [None]
        self.freqs = [None]
        self.extrapolate_left = extrapolate_left
        self.extrapolate_right = extrapolate_right
        self.transmission_coefs = None

    def prepend_01_point(self):
        self.freqs0 = np.concatenate((np.array([0]), self.freqs0))
        self.transmission_coefs0 = np.concatenate((np.array([1]),
                                                   self.transmission_coefs0))

    def resample(self, freqs):
        left = None
        right = None
        if freqs[0]<self.freqs0[0]:
            if self.extrapolate_left:
                left = self.transmission_coefs0[0]
            else:
                raise ValueError(
                    "New frequency array's lower limit is below the minimum"
                    " frequency in the network analyzer file."
                    " Adjust the new frequency array, or use extrapolation by"
                    " setting attribute extrapolate_left of this"
                    " TransmissionElement to True.")
        if freqs[-1] > self.freqs0[-1]:
            if self.extrapolate_right:
                right = self.transmission_coefs0[-1]
            else:
                raise ValueError(
                    "New frequency array's upper limit is above the maximum"
                    " frequency in the network analyzer file."
                    " Adjust the new frequency array, or use extrapolation by"
                    " setting attribute extrapolate_left of this"
                    " TransmissionElement to True.")
        self.transmission_coefs = np.interp(freqs, self.freqs0,
                                           self.transmission_coefs0, left=left,
                                           right=right)
        self.freqs = freqs

    @property
    def TransmissionCoefAbs(self):
        return np.absolute(self.transmission_coefs)

    @property
    def TransmissionCoefPhases(self):
        return np.angle(self.transmission_coefs, deg=True)


class Amplifier(TransmissionElement):
    def __init__(self, phase_shift_filename, dB_filename, T_amplifier_ns,
                 extrapolate_left=False, extrapolate_right=False,
                 prepend_01_point=False):
        super().__init__(extrapolate_left, extrapolate_right)
        self.T_amplifier_ns = T_amplifier_ns
        self.phase_shifts = pd.read_csv(phase_shift_filename, skiprows=2)
        self.dBs = pd.read_csv(dB_filename, skiprows=2)
        self.freqs0 = 1e-9*self.phase_shifts.iloc[:, 0].values
        exp_factor = np.exp(1j * np.radians(
                            self.phase_shifts.iloc[:, 1].values))
        self.G = exp_factor * np.power(10, self.dBs.iloc[:, 1].values / 20)
        aux_var = np.exp(2j * np.pi * self.T_amplifier_ns * self.freqs0)
        self.transmission_coefs0 = self.G * aux_var
        if prepend_01_point:
            self.prepend_01_point()
        # initializing self.freqs and self.transmission_coefs:
        self.resample(self.freqs0)


class Cable(TransmissionElement):
    def __init__(self, phase_shift_short_filename, dB_short_filename, 
                 phase_shift_open_filename, dB_open_filename, T_cable_ns,
                 T_cor_ns, extrapolate_left=False, extrapolate_right=False,
                 prepend_01_point=False):
        super().__init__(extrapolate_left, extrapolate_right)
        self.T_cable_ns = T_cable_ns
        self.T_cor_ns = T_cor_ns
        self.phase_shifts_short = pd.read_csv(phase_shift_short_filename,
                                              skiprows=2)
        self.dBs_short = pd.read_csv(dB_short_filename, skiprows=2)
        self.phase_shifts_open = pd.read_csv(phase_shift_open_filename,
                                             skiprows=2)
        self.dBs_open = pd.read_csv(dB_open_filename, skiprows=2)
        freqs_short = 1e-9*self.phase_shifts_short.iloc[:, 0].values
        freqs_open = 1e-9*self.phase_shifts_open.iloc[:, 0].values
        if sum(freqs_open-freqs_short) != 0:
            raise ValueError("Frequancy arrays for short and open cable"
                             " measurements do not match.")
        self.freqs0 = freqs_open
        exp_factor = -np.exp(1j*np.radians(
                             self.phase_shifts_short.iloc[:, 1].values))
        self.G_short = exp_factor\
            * np.power(10, self.dBs_short.iloc[:, 1].values / 20)
        self.G_open = np.exp(1j*np.radians(
            self.phase_shifts_open.iloc[:, 1].values)) \
            * np.power(10, self.dBs_open.iloc[:, 1].values / 20)
        self.TransmissionCoefs_short = self.G_short \
            * np.exp(2j*np.pi*self.T_cable_ns*self.freqs0)
        self.TransmissionCoefs_open = self.G_open \
            * np.exp(2j*np.pi*self.T_cable_ns*self.freqs0)
        self.transmission_coefs0 = np.sqrt(
            (self.TransmissionCoefs_short+self.TransmissionCoefs_open) / 2
            * np.exp(2j*np.pi*self.T_cor_ns*self.freqs0))
        if prepend_01_point:
            self.prepend_01_point()
        # initializing self.freqs and self.transmission_coefs:
        self.resample(self.freqs0)


# Theoretical modeling of cable transmission based on an equation:
class CableModel:
    """ z : in units of 100 ft
        k1 : in units of dB/100 ft/GHz^0.5
        k2 : in units of dB/100 ft/GHz"""
    def __init__(self, z, k1, k2):
        self.z = z
        self.k1 = k1
        self.k2 = k2
        self.transmission_coefs = None
        self.freqs = None

    def dB_to_linear(self, dB):
        return np.power(10, dB / 20)

    def calc_attenuation(self, f):
        """f: frequency in GHz
            f can be a single value or a numpy array"""
        return self.dB_to_linear(-(1. + 1.j) * self.k1 * self.z * np.sqrt(f)
                                 - self.k2 * self.z * f)

    def resample(self, freqs):
        self.transmission_coefs = self.calc_attenuation(freqs)
        self.freqs = freqs


class HeliaxCableHalfInch(CableModel):
    def __init__(self, z):
        super().__init__(z, 0.0642626*np.sqrt(1000), 0.188961)


class ColemanCableRG58(CableModel):
    def __init__(self, z):
        super().__init__(z, 0.0452387*np.sqrt(1000), 0.210059)


class SignalTransferLine():
    def __init__(self, transmission_elements, freqs=None):
        self.transmission_elements = transmission_elements
        self.transmission_coefs = None
        if freqs is not None:
            self.resample(freqs)

    @property
    def TransmissionCoefAbs(self):
        return np.absolute(self.transmission_coefs)

    @property
    def TransmissionCoefPhases(self):
        return np.angle(self.transmission_coefs, deg=True)

    def resample(self, freqs):
        res = 1
        for el in self.transmission_elements:
            el.resample(freqs)
            res = res*el.transmission_coefs
        self.freqs = freqs
        self.transmission_coefs = res


if __name__ == "__main__":
    freq_cutoff = 2  # GHz
    amplifier = Amplifier("TRACE40.csv", "TRACE41.csv", 2.7, True,
                          True, True)
    cable = Cable("TRACE15.csv", "TRACE16.csv", "TRACE20.csv", "TRACE21.csv",
                  2*0.229952e3, 0.26, True, True, True)
    cable_model = HeliaxCableHalfInch(3)
    freqs = np.linspace(0, freq_cutoff, 1e3)
    transfer_line = SignalTransferLine([cable, amplifier, cable_model],
                                       freqs=freqs)
