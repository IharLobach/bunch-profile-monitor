import numpy as np
from server_modules.config_requests import get_from_config
current_calibration_coef = get_from_config("current_calibration_coef")


class ErrorFWHMTooManyIntersections(Exception):
    pass


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


def get_signal_within_lims(y, time_arr, left_lim, right_lim):
    time_arr0 = time_arr[time_arr > left_lim]
    y_within_lims0 = y[time_arr > left_lim]
    y_within_lims = y_within_lims0[time_arr0 < right_lim]
    time_arr_within_limits = time_arr0[time_arr0 < right_lim]
    return time_arr_within_limits, y_within_lims


def calc_intersection_time(t1, y1, t2, y2, hm):
    return t1+(hm-y1)*(t2-t1)/(y2-y1)


@nan_support
def calc_fwhm(reconstructed_signal, time_arr, left_lim, right_lim):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    t, signal_within_lims = \
        get_signal_within_lims(reconstructed_signal, time_arr,
                               left_lim, right_lim)
    min_level = min(signal_within_lims)
    half_level = (min_level+average_level)/2
    y = signal_within_lims - half_level
    drop_last = y[:-1]
    drop_first = y[1:]
    mult = drop_last*drop_first
    intersections = np.argwhere(mult < 0).transpose()[0]
    if len(intersections) > 2:
        raise ErrorFWHMTooManyIntersections("FWHM: more than 2 intesrestions"
                                            " with half max level.")
    left_idx, right_idx = intersections
    left_t = calc_intersection_time(t[left_idx], y[left_idx],
                                    t[left_idx+1], y[left_idx+1], 0)
    right_t = calc_intersection_time(t[right_idx], y[right_idx],
                                     t[right_idx+1], y[right_idx+1], 0)
    fwhm = right_t-left_t
    return 30*fwhm


@nan_support
def calc_rms(reconstructed_signal, time_arr, left_lim, right_lim):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    y = reconstructed_signal-average_level
    time_arr_within_lims, y_within_lims = \
        get_signal_within_lims(y, time_arr, left_lim, right_lim)
    time_center = np.average(time_arr_within_lims, weights=-y_within_lims)
    variance = np.average((time_arr_within_lims-time_center)**2,
                          weights=-y_within_lims)
    rms = np.sqrt(variance)
    return 30*rms


@nan_support
def calc_phase_angle(reconstructed_signal, time_arr, t_RF):
    i_min = np.argmin(reconstructed_signal)
    delta_t = time_arr[i_min]-t_RF
    return delta_t/(133.0/4.0)/np.pi*180.0


@nan_support
def calc_current(reconstructed_signal, time_arr, left_lim, right_lim):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    y = reconstructed_signal-average_level
    time_arr_within_lims, y_within_lims = \
        get_signal_within_lims(y, time_arr, left_lim, right_lim)
    return current_calibration_coef*(-sum(y_within_lims))
