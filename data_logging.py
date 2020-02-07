import pandas as pd
import datetime
import time
import os
import sqlite3
import threading

def db_communication(func):
    def wrapper(*args,**kwargs):
        conn = sqlite3.connect('bunch-profile-monitor/log.db')
        c = conn.cursor()
        func(c,*args,**kwargs)
        # Save (commit) the changes
        conn.commit()
        conn.close()
    return wrapper

@db_communication
def add_record(c,tp):
    c.execute('INSERT INTO log VALUES (strftime("%Y-%m-%d %H:%M:%f","now","localtime"),?,?)', tp)

@db_communication
def delete_old_rows(c,logging_length):
    c.execute('DELETE FROM log WHERE date < datetime("now","localtime", "-{}")'.format(logging_length))

class data_logger_cleaner(threading.Thread):
    daemon = True
    
    def __init__(self,logging_length,cleaning_period_min):
        super().__init__()
        self.logging_length = logging_length
        self.cleaning_period_min = cleaning_period_min
    def run(self):
        while True:
            time.sleep(self.cleaning_period_min*60)
            delete_old_rows(self.logging_length)
    
    

    





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