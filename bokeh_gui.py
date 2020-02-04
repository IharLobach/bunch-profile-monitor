''' Present an interactive function explorer with slider widgets.

Scrub the sliders to change the properties of the ``sin`` curve, or
type into the title text box to update the title of the plot.

Use the ``bokeh serve`` command to run the example by executing:

    bokeh serve sliders.py

at your command prompt. Then navigate to the URL

    http://localhost:5006/sliders

in your browser.

'''
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, TextInput, Button
from bokeh.plotting import figure
from bokeh.events import ButtonClick
from bokeh.models import DataTable, DateFormatter, TableColumn


from BunchProfileMonitor import BunchProfileMonitor
from CableAmplifierTransferCoefs import Amplifier,Cable,SignalTransferLine,HeliaxCableHalfInch
from tcp_communication_with_scope import ConnectionToScope
import datetime
import threading
import queue
import pandas as pd
import os
import sys
import time
from bunch_profile_monitor_data_updater import bpm_data_updater
from initializations_for_gui import init_bpm_signal_transfer_line
from data_logging import save_full_plot_data

new_data_to_show_queue = queue.LifoQueue(1)
new_data_to_save_queue = queue.LifoQueue(1)

use_test_data = True
bpm,signal_transfer_line = init_bpm_signal_transfer_line(use_test_data)
t = bpm_data_updater(bpm, use_test_data, signal_transfer_line,new_data_to_show_queue,new_data_to_save_queue)
t.start()

# Set up data
x0 = np.arange(0,bpm.data_len*bpm.dt,bpm.dt)
y0 = bpm.reconstructed_signal
y0min = min(y0)
y0max = max(y0)
y0span = y0max - y0min
yadd = 0.1 * y0span
reconstructed_line_source = ColumnDataSource(data=dict(x=x0, y=y0))
y_original = bpm.v_arr
oscilloscope_line_source = ColumnDataSource(data=dict(x=x0, y=y_original))


# Set up plot
plot = figure(plot_height=400, plot_width=700, title="Last updated: {}".format(datetime.datetime.now()),
              tools="crosshair,pan,reset,save,wheel_zoom,box_zoom",
              x_range=[min(x0),max(x0)], y_range=[y0min-yadd, y0max+yadd])

plot.line('x', 'y', source=oscilloscope_line_source, line_width=3, line_alpha=0.6,color="green",legend_label="Original")
plot.line('x', 'y', source=reconstructed_line_source, line_width=3, line_alpha=0.6,color="red",legend_label="Reconstructed")
plot.legend.location = "bottom_right"
plot.title.text = "Last updated: {}".format(datetime.datetime.now())
plot.xaxis.axis_label = "Time, ns"
plot.yaxis.axis_label = "Signal from wall-current monitor, V"

# Set up widgets
saved_files_folder_text = TextInput(title="Files are saved to the following folder", value=
"bunch_profile_meas_{}".format(datetime.datetime.now().strftime("%m-%d-%Y")))
button_save_full_plot_data = Button(label="Save full plot data",button_type="success")
def button_save_full_plot_data_callback(event):
    save_full_plot_data(new_data_to_save_queue,saved_files_folder_text.value)
button_save_full_plot_data.on_event(ButtonClick,button_save_full_plot_data_callback)

#table
bpm.calc_fwhm()
table_data = dict(
        dates=["FFWHM, ns"],
        downloads=["{:.3f}".format(bpm.fwhm)],
    )
table_source = ColumnDataSource(table_data)

columns = [
        TableColumn(field="dates", title="Quantity"),
        TableColumn(field="downloads", title="Value"),
    ]
data_table = DataTable(source=table_source, columns=columns, width=300, height=280)



# Set up layouts and add to document
inputs = column(saved_files_folder_text,button_save_full_plot_data,data_table)

curdoc().add_root(row(inputs, plot, width=800))
curdoc().title = "IOTA Bunch Profile Monitor"

def try_update_plot():
    if not new_data_to_show_queue.empty():
        new_data = new_data_to_show_queue.get()
        reconstructed_signal = new_data["reconstructed_signal"] 
        original_signal =   new_data["oscilloscope_signal"]
        fwhm = new_data["fwhm"]
        table_data = dict(
        dates=["FWHM, ns"],
        downloads=["{:.3f}".format(fwhm)],
            )
        table_source = ColumnDataSource(table_data)
        data_table.source=table_source
        x = reconstructed_line_source.data["x"]
        y = reconstructed_signal
        reconstructed_line_source.data = dict(x=x, y=y)
        oscilloscope_line_source.data = dict(x=x,y=original_signal)
        plot.title.text = "Last updated: {}".format(datetime.datetime.now())

curdoc().add_periodic_callback(try_update_plot, 500)


    
