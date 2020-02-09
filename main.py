import numpy as np
import json

from bokeh.io import curdoc
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, Slider, TextInput, Button
from bokeh.plotting import figure
from bokeh.events import ButtonClick
from bokeh.models import DataTable, DateFormatter, TableColumn, Span


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
from bunch_length_estimators import calc_fwhm,calc_rms
from output_formatting import length_output
from config_requests import get_from_config
import data_logging
from data_logging import data_logger_cleaner

new_data_to_show_queue = queue.LifoQueue(1)
new_data_to_save_queue = queue.LifoQueue(1)


use_test_data = get_from_config("use_test_data")
bpm,signal_transfer_line = init_bpm_signal_transfer_line(use_test_data)
t = bpm_data_updater(bpm, use_test_data, signal_transfer_line,new_data_to_show_queue,new_data_to_save_queue)
t.start()

dlc_thread = data_logger_cleaner(logging_length=get_from_config("logging_length"),
cleaning_period_min=get_from_config("cleaning_period_min"))
dlc_thread.start()

acnet_logger = data_logging.ACNET_logger(get_from_config("clx_ip"),5005)





# Set up widgets
saved_files_folder_text = TextInput(title="Files are saved to the following folder", value=
"bunch_profile_meas_{}".format(datetime.datetime.now().strftime("%m-%d-%Y")),width=300)
button_save_full_plot_data = Button(label="Save full plot data",button_type="success",width=300)
def button_save_full_plot_data_callback(event):
    save_full_plot_data(new_data_to_save_queue,saved_files_folder_text.value)
button_save_full_plot_data.on_event(ButtonClick,button_save_full_plot_data_callback)


x0 = bpm.time_arr
x0max = max(x0)
x0min = min(x0)
minVal = length_output(get_from_config("left_rms_calc_limit"))#length_output(x0min+0.2*(x0max-x0min))
maxVal = length_output(get_from_config("right_rms_calc_limit"))#length_output(x0min+0.8*(x0max-x0min))
rms_calculation_min_text = TextInput(title="RMS calc. left limit", value=minVal,width=145)
rms_calculation_max_text = TextInput(title="RMS calc. right limit", value=maxVal,width=145)

#table
rms_left_lim = float(rms_calculation_min_text.value)
rms_right_lim = float(rms_calculation_max_text.value)
fwhm  = calc_fwhm(bpm.reconstructed_signal,bpm.time_arr,
        rms_left_lim,rms_right_lim
        )
rms = calc_rms(bpm.reconstructed_signal,bpm.time_arr,
        rms_left_lim,rms_right_lim)

table_data = dict(
        quantities=["FWHM, ns","RMS, ns"],
        values=[length_output(fwhm),length_output(rms)],
    )
table_source = ColumnDataSource(table_data)

columns = [
        TableColumn(field="quantities", title="Quantity"),
        TableColumn(field="values", title="Value"),
    ]
data_table = DataTable(source=table_source, columns=columns, width=300)



# Set up data
x0 = bpm.time_arr
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
              x_range=[min(x0),max(x0)], y_range=[y0min-yadd, y0max+yadd],
              sizing_mode = "scale_both")

plot.line('x', 'y', source=oscilloscope_line_source, line_width=3, line_alpha=0.6,color="green",legend_label="Original")
plot.line('x', 'y', source=reconstructed_line_source, line_width=3, line_alpha=0.6,color="red",legend_label="Reconstructed")
plot.legend.location = "bottom_right"
plot.title.text = "Last updated: {}".format(datetime.datetime.now())
plot.xaxis.axis_label = "Time, ns"
plot.yaxis.axis_label = "Signal from wall-current monitor, V"

rms_calc_left = float(rms_calculation_min_text.value)
rms_calc_left_span = Span(location=rms_calc_left,
                              dimension='height', line_color='green',
                              line_dash='dashed', line_width=3)
plot.add_layout(rms_calc_left_span)

rms_calc_right = float(rms_calculation_max_text.value)
rms_calc_right_span = Span(location=rms_calc_right,
                            dimension='height', line_color='red',
                            line_dash='dashed', line_width=3)
plot.add_layout(rms_calc_right_span)

def update_rms_calc_limits(attrname,old,new):
    rms_calc_left = float(rms_calculation_min_text.value)
    rms_calc_right = float(rms_calculation_max_text.value)
    rms_calc_left_span.location=rms_calc_left
    rms_calc_right_span.location=rms_calc_right

for w in [rms_calculation_min_text,rms_calculation_max_text]:
    w.on_change('value',update_rms_calc_limits)

# Set up layouts and add to document
inputs = column(saved_files_folder_text,button_save_full_plot_data,
row(rms_calculation_min_text,rms_calculation_max_text),data_table)


curdoc().add_root(row(inputs,plot))
curdoc().title = "IOTA Bunch Profile Monitor"

def try_update_plot():
    if not new_data_to_show_queue.empty():
        new_data = new_data_to_show_queue.get()
        reconstructed_signal = new_data["reconstructed_signal"] 
        original_signal =   new_data["oscilloscope_signal"]
        rms_left_lim = float(rms_calculation_min_text.value)
        rms_right_lim = float(rms_calculation_max_text.value)
        fwhm = calc_fwhm(reconstructed_signal,bpm.time_arr,rms_left_lim,rms_right_lim)
        rms = calc_rms(reconstructed_signal,bpm.time_arr,rms_left_lim,rms_right_lim)
        table_data = dict(
        quantities=["FWHM, ns","RMS, ns"],
        values=[length_output(fwhm),length_output(rms)])
        table_source.data = table_data
        data_logging.add_record((fwhm,rms))
        acnet_logger.send_to_ACNET(fwhm,rms)
        x = reconstructed_line_source.data["x"]
        y = reconstructed_signal
        reconstructed_line_source.data = dict(x=x, y=y)
        oscilloscope_line_source.data = dict(x=x,y=original_signal)
        plot.title.text = "Last updated: {}".format(datetime.datetime.now())
        #print("Last updated: {}".format(datetime.datetime.now()))

curdoc().add_periodic_callback(try_update_plot, 500)


    
