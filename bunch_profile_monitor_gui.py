import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from BunchProfileMonitor import BunchProfileMonitor
from CableAmplifierTransferCoefs import Amplifier,Cable,SignalTransferLine,HeliaxCableHalfInch
from tcp_communication_with_scope import ConnectionToScope
import datetime
import threading
import queue
import numpy as np
import pandas as pd
import os
import sys
import time
from bunch_profile_monitor_data_updater import bpm_data_updater





class App:
    def __init__(self):
        self.new_data_to_show_queue = queue.LifoQueue(1)
        self.new_data_to_save_queue = queue.LifoQueue(1)

    def init_signal_transfer_line(self,freqs):
        #cwd = os.getcwd()
        def resource_path(relative_path):
            """ Get absolute path to resource, works for dev and for PyInstaller """
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except:
                base_path = os.environ.get("_MEIPASS2",os.path.abspath("."))
            return os.path.join(base_path, relative_path)
        file_names = ["TRACE40.csv","TRACE41.csv","TRACE15.csv","TRACE16.csv","TRACE20.csv","TRACE21.csv"]
        p0,p1,p2,p3,p4,p5 = [resource_path(os.path.join("signal_transfer_line_data",fn)) for fn in file_names]
        amplifier = Amplifier(p0,p1,2.7,True,True,True)
        cable = Cable(p2,p3,p4,p5,2*0.229952e3,0.26,True,True,True)
        # Test with no attenuation or dispersion:
        #cable_model = HeliaxCableHalfInch(0)
        #return SignalTransferLine([cable_model],freqs) 
        return SignalTransferLine([cable,amplifier],freqs)

    def init_bpm_signal_transfer_line(self, useTestData):
        conn = ConnectionToScope()
        bpm = BunchProfileMonitor(connection_to_scope=conn,dt=0.1)
        attempt = 0
        while True:
            if attempt > 5:
                raise Exception('Attempted to connect to the scope 5 times. No luck.')
            if bpm.update_data(testing=useTestData):
                break
            attempt += 1
        bpm.perform_fft()
        signal_transfer_line = self.init_signal_transfer_line(bpm.fourier_frequencies)
        bpm.transmission_coefs = signal_transfer_line.TransmissionCoefs
        bpm.perform_signal_reconstruction()
        return bpm,signal_transfer_line

    def init_fig(self,bpm):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time, ns")
        self.ax.set_ylabel("Reconstructed signal from wall-current monitor, V")
        x0 = np.arange(0,bpm.data_len*bpm.dt,bpm.dt)
        y0 = bpm.reconstructed_signal
        y0min = min(y0)
        y0max = max(y0)
        y0span = y0max - y0min
        yadd = 0.1 * y0span
        self.ax.set_ylim(y0min - yadd, y0max + yadd)
        self.line, = self.ax.plot(x0, y0, marker='o', color='orange')
        self.ax.grid()

    def init_control_panel(self):
        self.control_panel_canvas = tkinter.Canvas(self.root, width = 1000, height = 300)
        self.control_panel_canvas.pack()

        # X-Y lims:
        self.x_lim_min = tkinter.Entry (self.root) 
        self.x_lim_min.insert(0,"{:.3f}".format(self.ax.get_xlim()[0]))
        self.control_panel_canvas.create_window(100, 100, window=self.x_lim_min)
        self.control_panel_canvas.create_window(100, 80, window=tkinter.Label(self.root, text="Xmin, ns"))
        self.x_lim_max = tkinter.Entry (self.root)
        self.x_lim_max.insert(0,"{:.3f}".format(self.ax.get_xlim()[1]))
        self.control_panel_canvas.create_window(250, 100, window=self.x_lim_max)
        self.control_panel_canvas.create_window(250, 80, window=tkinter.Label(self.root, text="Xmax, ns"))
        self.y_lim_min = tkinter.Entry (self.root)
        self.y_lim_min.insert(0,"{:.3f}".format(self.ax.get_ylim()[0]))
        self.control_panel_canvas.create_window(100, 50, window=self.y_lim_min)
        self.control_panel_canvas.create_window(100, 30, window=tkinter.Label(self.root, text="Ymin, ns"))
        self.y_lim_max = tkinter.Entry (self.root) 
        self.y_lim_max.insert(0,"{:.3f}".format(self.ax.get_ylim()[1]))
        self.control_panel_canvas.create_window(250, 50, window=self.y_lim_max)
        self.control_panel_canvas.create_window(250, 30, window=tkinter.Label(self.root, text="Ymax, ns"))

        self.change_xy_lim_button = tkinter.Button(text='Apply changes', command=self.change_xy_lim)
        self.control_panel_canvas.create_window(175, 150, window=self.change_xy_lim_button)

        # FWHM:
        self.control_panel_canvas.create_window(500, 30, window=tkinter.Label(self.root, text="FWHM, ns"))
        self.fwhm_textvariable = tkinter.StringVar()
        self.fwhm_label = tkinter.Label(self.root, textvariable = self.fwhm_textvariable)
        self.control_panel_canvas.create_window(500, 50, window=self.fwhm_label)

        # Saving file window:
        self.saved_file_folder = tkinter.Entry (self.root,width=50) 
        self.saved_file_folder.insert(0,"bunch_profile_meas_{}".format(datetime.datetime.now().strftime("%m-%d-%Y")))
        self.control_panel_canvas.create_window(800, 50, window=self.saved_file_folder)
        self.control_panel_canvas.create_window(800, 30, window=tkinter.Label(self.root, text="Waveforms are saved to:"))
        self.save_file_button = tkinter.Button(text='Save waveform', command=self.save_file)
        self.control_panel_canvas.create_window(800, 150, window=self.save_file_button)

    def prep_data_to_save(self,data_to_save_dict):
        return pd.DataFrame({"oscilloscope_signal":data_to_save_dict["oscilloscope_signal"],
        "reconstructed_signal":data_to_save_dict["reconstructed_signal"]})

    def save_file(self):
        t1 = time.time()
        while True:
            if not self.new_data_to_save_queue.empty():
                new_data_to_save = self.new_data_to_save_queue.get()
                df = self.prep_data_to_save(new_data_to_save)
                t = datetime.datetime.now()
                folder_name = self.saved_file_folder.get()
                if not os.path.exists(folder_name):
                    os.mkdir(folder_name)
                file_path = os.path.join(folder_name,
                "bunch_profile_{}.csv".format(t.strftime("%m-%d-%Y_%H_%M_%S_%f")))
                df.to_csv(file_path)
                break
            if time.time()-t1>1:
                # Failed to save waveform
                break

    def init_tkinter(self):
        # initialise a window.
        self.root = tkinter.Tk()
        self.root.config(background='white')
        self.root.geometry("1000x700")
        lab = tkinter.Label(self.root, text="Bunch profile monitor", bg='white').pack()
        self.graph = FigureCanvasTkAgg(self.fig, master=self.root)
        self.graph.get_tk_widget().pack(side="top", fill='both', expand=True)
    
    def change_xy_lim(self):  
        try:
            self.ax.set_xlim(float(self.x_lim_min.get()),float(self.x_lim_max.get()))
            self.ax.set_ylim(float(self.y_lim_min.get()),float(self.y_lim_max.get()))
        except:
            pass

    def try_update_plot(self):
         if not self.new_data_to_show_queue.empty():
            new_data = self.new_data_to_show_queue.get()
            reconstructed_signal = new_data["reconstructed_signal"]   
            fwhm = new_data["fwhm"]
            self.line.set_ydata(reconstructed_signal)
            self.fwhm_textvariable.set("{:.3f}".format(fwhm))
            self.ax.set_title("Last updated: {}".format(datetime.datetime.now()))
            self.graph.draw()

         self.root.after(200, self.try_update_plot)

    def run(self,use_test_data = False):
        bpm,signal_transfer_line = self.init_bpm_signal_transfer_line(use_test_data)
        self.init_fig(bpm)
        self.init_tkinter()
        self.init_control_panel()
        t = bpm_data_updater(bpm, use_test_data, signal_transfer_line,self.new_data_to_show_queue,self.new_data_to_save_queue)
        t.start()
        self.root.after(100, self.try_update_plot)
        self.root.mainloop()



if __name__ == '__main__':
    app = App()
    app.run(use_test_data=True)