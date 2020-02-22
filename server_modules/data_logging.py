import pandas as pd
import datetime
import time
import os
import sqlite3
import threading
import socket


def db_communication(func):
    def wrapper(*args, **kwargs):
        try:
            conn = sqlite3.connect(os.path.join(os.getcwd(),
                                   'bunch-profile-monitor', 'log.db'))
            c = conn.cursor()
            func(c, *args, **kwargs)
            # Save (commit) the changes
            conn.commit()
            conn.close()
        except Exception as e:
            print("Exception happened while communicating"
                  " with the database at {}".format(datetime.datetime.now()))
            print(e)
    return wrapper


@db_communication
def add_record(c, tp):
    sql_command = '''INSERT INTO log
    VALUES (strftime("%Y-%m-%d %H:%M:%f","now","localtime"),?,?,?,?,?,?)'''
    c.execute(sql_command, tp)


@db_communication
def delete_old_rows(c, logging_length):
    c.execute('DELETE FROM log WHERE date < datetime("now","localtime", "-{}")'
              .format(logging_length))


class data_logger_cleaner(threading.Thread):
    daemon = True

    def __init__(self, logging_length, cleaning_period_min):
        super().__init__()
        self.logging_length = logging_length
        self.cleaning_period_min = cleaning_period_min

    def run(self):
        while True:
            time.sleep(self.cleaning_period_min*60)
            delete_old_rows(self.logging_length)


class ACNET_logger():
    def __init__(self, UDP_IP, UDP_PORT):
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_to_ACNET(self, fwhm, rms):
        MESSAGE = "{}|{}".format(fwhm, rms)
        self.sock.sendto(MESSAGE.encode(), (self.UDP_IP, self.UDP_PORT))


def prep_data_to_save(data_to_save_dict):
    return pd.DataFrame(
        {
            "oscilloscope_signal": data_to_save_dict["oscilloscope_signal"],
            "reconstructed_signal": data_to_save_dict["reconstructed_signal"]
        })


def save_full_plot_data(new_data_to_save_queue, saved_file_folder):
    t1 = time.time()
    while True:
        if not new_data_to_save_queue.empty():
            new_data_to_save = new_data_to_save_queue.get()
            df = prep_data_to_save(new_data_to_save)
            t = datetime.datetime.now()
            all_meas_folder = \
                os.path.join(os.getcwd(),
                             "measurements-bunch-profile-monitor")
            if not os.path.exists(all_meas_folder):
                os.mkdir(all_meas_folder)
            folder_name = os.path.join(all_meas_folder, saved_file_folder)
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
            file_name = "bunch_profile_{}.csv".format(t.strftime(
                                                      "%m-%d-%Y_%H_%M_%S_%f"))
            file_path = os.path.join(folder_name, file_name)
            df.to_csv(file_path)
            break
        if time.time()-t1 > 1:
            # Failed to save waveform
            break
