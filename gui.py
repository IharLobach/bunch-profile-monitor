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
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.set_xlabel("Time, ns")
        ax.set_ylabel("Reconstructed signal from wall-current monitor, V")
        x0 = np.arange(0,bpm.data_len*bpm.dt,bpm.dt)
        y0 = bpm.reconstructed_signal
        y0min = min(y0)
        y0max = max(y0)
        y0span = y0max - y0min
        yadd = 0.1 * y0span
        ax.set_ylim(y0min - yadd, y0max + yadd)
        line, = ax.plot(x0, y0, marker='o', color='orange')
        ax.grid()
        return fig, ax, line

    def init_tkinter(self,fig):
        # initialise a window.
        root = tkinter.Tk()
        root.config(background='white')
        root.geometry("1000x700")
        lab = tkinter.Label(root, text="Bunch profile monitor", bg='white').pack()
        graph = FigureCanvasTkAgg(fig, master=root)
        graph.get_tk_widget().pack(side="top", fill='both', expand=True)
        return root, graph

    def try_update_plot(self,line, ax, graph, root):
         if not self.new_data_queue.empty():
            new_data = self.new_data_queue.get()
            #line.set_xdata(new_data[0])
            line.set_ydata(new_data)
            ax.set_title("Last updated: {}".format(datetime.datetime.now()))
            graph.draw()
            # with self.new_data_queue.mutex:
            #     self.new_data_queue.queue.clear()
         root.after(100, self.try_update_plot, line, ax, graph, root)

    def run(self,use_test_data = False):
        bpm,signal_transfer_line = self.init_bpm_signal_transfer_line(use_test_data)
        fig, ax, line = self.init_fig(bpm)
        root, graph = self.init_tkinter(fig)
        t = bpm_data_updater(bpm, use_test_data, signal_transfer_line,self.new_data_queue)
        t.start()
        root.after(100, self.try_update_plot, line, ax, graph, root)
        root.mainloop()



if __name__ == '__main__':
    app = App()
    app.run(use_test_data=True)