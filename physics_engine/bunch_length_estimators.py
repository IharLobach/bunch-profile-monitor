import numpy as np
from server_modules.config_requests import get_from_config
from scipy.optimize import curve_fit
current_calibration_coef = get_from_config("current_calibration_coef")
noise_range = get_from_config("range_noise_level_calculation_ns")


class ErrorFWHMTooManyIntersections(Exception):
    pass


def calc_average_level(reconstructed_signal, time_arr, left_lim, right_lim):
    left = reconstructed_signal[
        (time_arr < left_lim) & (time_arr > left_lim - noise_range)]
    right = reconstructed_signal[
        (time_arr > right_lim) & (time_arr < right_lim + noise_range)]
    both_sides = np.concatenate([left, right])
    return np.mean(both_sides)


def nan_support(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print("In nan_support: ", e)
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
def calc_phase_angle(reconstructed_signal, time_arr, left_lim, right_lim,
                     iota_freq_MHz):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    y = reconstructed_signal-average_level
    time_arr_within_lims, y_within_lims = \
        get_signal_within_lims(y, time_arr, left_lim, right_lim)
    time_center = np.average(time_arr_within_lims, weights=-y_within_lims)
    # i_min = np.argmin(reconstructed_signal)
    # delta_t = time_arr[i_min]
    delta_t = time_center
    return delta_t*4*iota_freq_MHz/1000/np.pi*180.0


@nan_support
def calc_current(reconstructed_signal, time_arr, left_lim, right_lim):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    y = reconstructed_signal-average_level
    time_arr_within_lims, y_within_lims = \
        get_signal_within_lims(y, time_arr, left_lim, right_lim)
    return -current_calibration_coef/0.1*(right_lim-left_lim) \
        * (-np.mean(y_within_lims))


@nan_support
def calc_fur_length(reconstructed_signal, time_arr, left_lim, right_lim):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    y = reconstructed_signal-average_level
    time_arr_within_lims, y_within_lims = \
        get_signal_within_lims(y, time_arr, left_lim, right_lim)
    return 30*(right_lim-left_lim)/2/np.sqrt(np.pi)\
        * (np.mean(y_within_lims)*np.sum(y_within_lims))\
        / np.sum(y_within_lims**2)


@nan_support
def calc_mad_length(reconstructed_signal, time_arr, left_lim, right_lim):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    y = reconstructed_signal-average_level
    time_arr_within_lims, y_within_lims = \
        get_signal_within_lims(y, time_arr, left_lim, right_lim)
    time_center = np.average(time_arr_within_lims, weights=-y_within_lims)
    mad = np.average(np.absolute(time_arr_within_lims-time_center),
                          weights=-y_within_lims)
    return 30*mad


def calc_ramsg_currentg(reconstructed_signal, time_arr, left_lim, right_lim,
                        fwhm, fit_points=None):
    average_level = calc_average_level(reconstructed_signal, time_arr,
                                       left_lim, right_lim)
    y = reconstructed_signal-average_level
    time_arr_within_lims, y_within_lims = \
        get_signal_within_lims(y, time_arr, left_lim, right_lim)
    i_min = np.argmin(y_within_lims)
    t_min = time_arr_within_lims[i_min]
    A0 = y_within_lims[i_min]
    mu0 = t_min
    sigma0 = fwhm/2.3551
    p0 = (A0, mu0, sigma0)

    def gauss(t, *p):
        A, mu, sigma = p
        return A*np.exp(-(t-mu)**2/(2.*sigma**2))

    t1 = t_min-fwhm
    t2 = t_min+fwhm
    coeff, var_matrix = curve_fit(gauss, time_arr_within_lims, y_within_lims,
                                  p0=p0,
                                  bounds=([2*A0, t1, 0], [0, t2, 2*fwhm]))
    Af, muf, sigmaf = coeff
    sigmaf = np.absolute(sigmaf)
    plot_data = None
    if fit_points:
        x_data = np.linspace(time_arr_within_lims[0], time_arr_within_lims[-1],
                             fit_points)
        y_data = average_level+gauss(x_data, Af, muf, sigmaf)
        plot_data = (x_data, y_data)
    return 30*sigmaf, current_calibration_coef/0.1*Af*np.sqrt(2*np.pi)*sigmaf,\
        plot_data
