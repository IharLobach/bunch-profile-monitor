import numpy as np


def calc_average_level(reconstructed_signal, time_arr, left_lim, right_lim):
    left = reconstructed_signal[time_arr < left_lim]
    right = reconstructed_signal[time_arr > right_lim]
    both_sides = np.concatenate([left, right])
    return np.mean(both_sides)


def nan_support(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return "nan"
    return wrapper


@nan_support
def calc_fwhm(reconstructed_signal, time_arr, left_lim, right_lim):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    min_level = min(reconstructed_signal)
    half_level = (min_level+average_level)/2
    y = reconstructed_signal - half_level
    y_01 = np.where(y < 0, 1, 0)
    dt = (time_arr[-1]-time_arr[0])/(len(time_arr)-1)
    fwhm = sum(y_01)*dt
    return fwhm


@nan_support
def calc_rms(reconstructed_signal, time_arr, left_lim, right_lim):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    y = reconstructed_signal-average_level
    y_within_lims0 = np.where(time_arr > left_lim, y, 0)
    y_within_lims = np.where(time_arr < right_lim, y_within_lims0, 0)
    time_center = np.average(time_arr, weights=-y_within_lims)
    variance = np.average((time_arr-time_center)**2, weights=-y_within_lims)
    rms = np.sqrt(variance)
    return rms
