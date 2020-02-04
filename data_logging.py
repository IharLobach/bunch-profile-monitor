import pandas as pd
import datetime
import time
import os


def prep_data_to_save(data_to_save_dict):
    return pd.DataFrame({"oscilloscope_signal":data_to_save_dict["oscilloscope_signal"],
    "reconstructed_signal":data_to_save_dict["reconstructed_signal"]})

def save_full_plot_data(new_data_to_save_queue,saved_file_folder):
    t1 = time.time()
    while True:
        if not new_data_to_save_queue.empty():
            new_data_to_save = new_data_to_save_queue.get()
            df = prep_data_to_save(new_data_to_save)
            t = datetime.datetime.now()
            folder_name = saved_file_folder
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
            file_path = os.path.join(folder_name,
            "bunch_profile_{}.csv".format(t.strftime("%m-%d-%Y_%H_%M_%S_%f")))
            df.to_csv(file_path)
            break
        if time.time()-t1>1:
            # Failed to save waveform
            break