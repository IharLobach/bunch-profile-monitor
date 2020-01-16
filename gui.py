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
import os



class bpm_data_updater(threading.Thread):
    daemon = True

    def __init__(self, bpm,use_test_data,signal_transfer_line,new_data_queue):
        super().__init__()
        self.bpm = bpm
        self.use_test_data = use_test_data
        self.signal_transfer_line = signal_transfer_line
        self.new_data_queue = new_data_queue

    def run(self):
        while True:
            update_successful = self.bpm.update_data(testing=self.use_test_data)
            self.bpm.perform_fft()
            self.bpm.perform_signal_reconstruction()
            if update_successful:
                with self.new_data_queue.mutex:
                    self.new_data_queue.queue.clear()
                self.new_data_queue.put(self.bpm.reconstructed_signal)

class App:
    def __init__(self):
        self.new_data_queue = queue.LifoQueue(1)

    def init_signal_transfer_line(self,freqs):
        cwd = os.getcwd()
        file_names = ["TRACE40.csv","TRACE41.csv","TRACE15.csv","TRACE16.csv","TRACE20.csv","TRACE21.csv"]
        p0,p1,p2,p3,p4,p5 = [os.path.join(cwd,"signal_transfer_line_data",fn) for fn in file_names]
        amplifier = Amplifier(p0,p1,2.7,True,True,True)
        cable = Cable(p2,p3,p4,p5,2*0.229952e3,0.26,True,True,True)
        # Test with no attenuation or dispersion:
        #cable_model = HeliaxCableHalfInch(0)
        #return SignalTransferLine([cable_model],freqs) 
        return SignalTransferLine([cable,amplifier],freqs)

    def init_bpm_signal_transfer_line(self, useTestData):
        conn = ConnectionToScope()
        bpm = BunchProfileMonitor(connection_to_scope=conn,dt=0.2)
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
         if not self.new_data_queue.empty():
            new_data = self.new_data_queue.get()
            #line.set_xdata(new_data[0])
            # try:
            #     self.ax.set_xlim(0,self.x1)
            # except:
            #     pass
            self.line.set_ydata(new_data)
            self.ax.set_title("Last updated: {}".format(datetime.datetime.now()))
            self.graph.draw()
            # with self.new_data_queue.mutex:
            #     self.new_data_queue.queue.clear()
         self.root.after(200, self.try_update_plot)

    def run(self,use_test_data = False):
        bpm,signal_transfer_line = self.init_bpm_signal_transfer_line(use_test_data)
        self.init_fig(bpm)
        self.init_tkinter()
        self.init_control_panel()
        t = bpm_data_updater(bpm, use_test_data, signal_transfer_line,self.new_data_queue)
        t.start()
        self.root.after(100, self.try_update_plot)
        self.root.mainloop()



if __name__ == '__main__':
    app = App()
    app.run(use_test_data=True)