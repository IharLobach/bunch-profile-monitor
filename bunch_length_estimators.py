import numpy as np
def calc_average_level(reconstructed_signal,time_arr,left_lim,right_lim):
    outsiders0 = np.where(time_arr>right_lim,reconstructed_signal,0)
    outsiders = np.where(time_arr<left_lim,reconstructed_signal,outsiders0)
    return np.mean(outsiders)


def calc_fwhm(reconstructed_signal,time_arr,left_lim,right_lim):
    average_level = calc_average_level(reconstructed_signal,time_arr,left_lim,right_lim)
    min_level = min(reconstructed_signal)
    half_level = (min_level+average_level)/2
    y = reconstructed_signal - half_level
    y_01 = np.where(y<0,1,0)
    dt = (time_arr[-1]-time_arr[0])/(len(time_arr)-1)
    fwhm = sum(y_01)*dt
    return fwhm

def calc_rms(reconstructed_signal,time_arr,left_lim,right_lim):
    average_level = calc_average_level(reconstructed_signal,time_arr,left_lim,right_lim)
    #print("avrage level = {}".format(average_level))
    y = reconstructed_signal-average_level
    y_within_lims0 = np.where(time_arr>left_lim,y,0)
    y_within_lims = np.where(time_arr<right_lim,y_within_lims0,0)
    time_center = np.average(time_arr,weights=-y_within_lims)
    #print("time_center = {}".format(time_center))
    variance = np.average((time_arr-time_center)**2,weights=-y_within_lims)
    #print("variance = {}".format(variance))
    rms = np.sqrt(variance)
    return rms