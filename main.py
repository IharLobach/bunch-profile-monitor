import numpy as np
import json

from bokeh.io import curdoc
from bokeh.layouts import column, row, layout
from bokeh.models import \
     ColumnDataSource, Slider, TextInput, Button, Div, Toggle
from bokeh.plotting import figure
from bokeh.events import ButtonClick
from bokeh.models import DataTable, DateFormatter, TableColumn, Span


from server_modules.tcp_communication_with_scope import ConnectionToScope
import datetime
import threading
import queue
import pandas as pd
import os
import sys
import signal
import time
from server_modules.bunch_profile_monitor_data_updater import bpm_data_updater
from server_modules.initializations_for_gui import \
     init_bpm_signal_transfer_line
from server_modules.data_logging import save_full_plot_data
from physics_engine.bunch_length_estimators import \
    calc_fwhm, calc_rms, calc_phase_angle, calc_current
from server_modules.output_formatting import length_output
from server_modules.config_requests import get_from_config
import server_modules.data_logging as data_logging
from server_modules.data_logging import data_logger_cleaner
from server_modules.tcp_communication_with_scope import ConnectionToScope


use_test_data = get_from_config("use_test_data")
if not use_test_data:
    conn = ConnectionToScope()
else:
    conn = None
bpm, signal_transfer_line = init_bpm_signal_transfer_line(use_test_data, conn)


def sigint_handler(signal, frame):
    if conn:
        print("Closing connection to the scope.")
        conn.close()
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)


t_RF_ns = get_from_config("t_RF_ns")

dlc_thread = data_logger_cleaner(
    logging_length=get_from_config("logging_length"),
    cleaning_period_min=get_from_config("cleaning_period_min"))
dlc_thread.start()

acnet_logger = data_logging.ACNET_logger(get_from_config("clx_ip"), 5005)

saved_files_folder_text = TextInput(
    title="Files are saved to the following folder",
    value="bunch_profile_meas_{}".format(datetime.datetime.now()
                                         .strftime("%m-%d-%Y")),
    width=300)
button_save_full_plot_data = Button(
    label="Save full plot data",
    button_type="success",
    width=300)

div_rms = Div(text="Calculation limits (ns) for RMS length and Current:",
              width=300)

toggle_rms = Toggle(label="Manual/Auto", button_type="success",
                    width=300, active=get_from_config("rms_lims_auto"))

rms_calculation_min_text = TextInput(
    value=length_output(get_from_config("x_range")[0]), width=145)
rms_calculation_max_text = TextInput(
    value=length_output(get_from_config("x_range")[1]), width=145)

table_source = ColumnDataSource()

columns = [
        TableColumn(field="quantities", title="Quantity"),
        TableColumn(field="values", title="Value"),
    ]
data_table = DataTable(source=table_source, columns=columns,
                       width=300, height=160)

reconstructed_line_source = ColumnDataSource(dict(x=[], y=[]))
oscilloscope_line_source = ColumnDataSource(dict(x=[], y=[]))


def button_save_full_plot_data_callback(event):
    save_full_plot_data(
        {
            "oscilloscope_signal": oscilloscope_line_source.data['y'],
            "reconstructed_signal": reconstructed_line_source.data['y']
        }, saved_files_folder_text.value)


button_save_full_plot_data.on_event(ButtonClick,
                                    button_save_full_plot_data_callback)
# Set up plot
plot = figure(plot_height=400, plot_width=700,
              title="Last updated: {}".format(datetime.datetime.now()),
              tools="crosshair,pan,reset,save,wheel_zoom,box_zoom",
              x_range=get_from_config("x_range"),
              y_range=get_from_config("y_range"),
              sizing_mode="scale_both")

plot.line('x', 'y', source=oscilloscope_line_source, line_width=3,
          line_alpha=0.6, color="green", legend_label="Original")
plot.line('x', 'y', source=reconstructed_line_source, line_width=3,
          line_alpha=0.6, color="red", legend_label="Reconstructed")
plot.legend.location = "bottom_right"
plot.title.text = "Last updated: {}".format(datetime.datetime.now())
plot.xaxis.axis_label = "Time, ns"
plot.yaxis.axis_label = "Signal from wall-current monitor, V"


rms_calc_left_span = Span(location=get_from_config("x_range")[0],
                          dimension='height', line_color='green',
                          line_dash='dashed', line_width=3)
plot.add_layout(rms_calc_left_span)

rms_calc_right_span = Span(location=get_from_config("x_range")[1],
                           dimension='height', line_color='red',
                           line_dash='dashed', line_width=3)
plot.add_layout(rms_calc_right_span)

# vertical span of the oscilloscope

div = Div(text="Oscilloscope's vertical scale:", width=300)

toggle = Toggle(label="Manual/Auto", button_type="success",
                width=300, active=get_from_config("vertical_scale_auto"))


if toggle.active:
    offset = conn.get_offset()
    volt_div = conn.get_volt_div()
    half_span = volt_div*4
    top = half_span-offset
    bottom = -offset-half_span
else:
    bottom, top = get_from_config("y_range")

top_span = Span(location=top,
                dimension='width', line_color='blue',
                line_dash='dashed', line_width=3)
plot.add_layout(top_span)
bottom_span = Span(location=bottom,
                   dimension='width', line_color='blue',
                   line_dash='dashed', line_width=3)
plot.add_layout(bottom_span)


def update_vertical_span():
    offset = conn.get_offset()
    print("offset = ", offset)
    volt_div = conn.get_volt_div()
    half_span = volt_div*4
    top = half_span-offset
    bottom = -offset-half_span
    top_span.location = top
    bottom_span.location = bottom


button_increase = Button(
    label="Increase",
    button_type="success",
    width=145)

toggle_increase = Toggle(label="Increase", button_type="success",
                         width=145,
                         active=False)


def button_increase_callback(event):
    volt_div = conn.get_volt_div()
    if volt_div == 2.5:
        pass
    else:
        target = min(volt_div*2, 2.5)
        print("target = ", target)
        while True:
            conn.set_volt_div(target)
            print("set")
            vd = conn.get_volt_div()
            print("vd = ", vd)
            if vd == target:
                break
    update_vertical_span()


toggle_decrease = Toggle(label="Decrease", button_type="success",
                         width=145,
                         active=False)


def button_decrease_callback(event):
    volt_div = conn.get_volt_div()
    print("volt_div = ", volt_div)
    if volt_div == 0.002:
        pass
    else:
        target = max(volt_div*0.5, 0.002)
        print("target = ", target)
        while True:
            conn.set_volt_div(target)
            print("set")
            vd = conn.get_volt_div()
            print(vd)
            if vd == target:
                break
    update_vertical_span()


def check_if_need_update_vertical_span(original_signal):
    m = min(original_signal)
    if (m > -0.010) and (bottom_span.location > -0.040):
        return 0
    elif m > -5.0:
        if m < 0.9*bottom_span.location:
            return 1
        elif m > 0.9*bottom_span.location*0.5:
            return -1
    else:
        return 0


# end vertical span of the oscilloscope

cutoff_slider = Slider(
    start=0,
    end=max(bpm.fourier_frequencies),
    value=max(bpm.fourier_frequencies)/2,
    step=.1,
    title="Freq. Cutoff for Transmission Coefficients, GHz")


def inputs_callback(attrname, old, new):
    if not toggle_rms.active:
        rms_calc_left = float(rms_calculation_min_text.value)
        rms_calc_right = float(rms_calculation_max_text.value)
        rms_calc_left_span.location = rms_calc_left
        rms_calc_right_span.location = rms_calc_right
    bpm.transmission_coefs = \
        np.where(bpm.fourier_frequencies < cutoff_slider.value,
                 signal_transfer_line.transmission_coefs, 1)


for w in [rms_calculation_min_text, rms_calculation_max_text, cutoff_slider]:
    w.on_change('value', inputs_callback)

# Set up layouts and add to document
rms_calc_row = row(rms_calculation_min_text, rms_calculation_max_text)
inputs = column(saved_files_folder_text, button_save_full_plot_data,
                div_rms, toggle_rms,
                rms_calc_row, data_table, cutoff_slider, div, toggle,
                row(toggle_decrease, toggle_increase))


curdoc().add_root(row(inputs, plot))
curdoc().title = "IOTA Bunch Profile Monitor"

low_signal_limit = get_from_config("low_signal_lim_V")
mbl = get_from_config("max_bunch_length_ns")

rms_window = get_from_config("rms_window_size")


def try_update_plot():
    try:
        update_successful = bpm.update_data(testing=use_test_data)
        bpm.perform_fft()
        bpm.perform_signal_reconstruction()
        reconstructed_signal = bpm.reconstructed_signal
        original_signal = bpm.v_arr
        i_min = np.argmin(reconstructed_signal)
        t_min = bpm.time_arr[i_min]
        if min(original_signal) > -low_signal_limit:
            fwhm = rms = phase_angle = current = "nan"
        else:
            fwhm = calc_fwhm(reconstructed_signal, bpm.time_arr,
                             t_min-mbl, t_min+mbl)
            if toggle_rms.active and (fwhm != 'nan'):
                rms_left_lim = t_min-rms_window*fwhm/30
                rms_right_lim = t_min+rms_window*fwhm/30
                rms_calc_left_span.location = rms_left_lim
                rms_calc_right_span.location = rms_right_lim
                rms_calculation_min_text.value = length_output(rms_left_lim)
                rms_calculation_max_text.value = length_output(rms_right_lim)
            rms = calc_rms(reconstructed_signal, bpm.time_arr,
                           rms_calc_left_span.location,
                           rms_calc_right_span.location)
            phase_angle = calc_phase_angle(reconstructed_signal, bpm.time_arr,
                                           t_RF_ns)
            current = calc_current(reconstructed_signal, bpm.time_arr,
                                   rms_calc_left_span.location,
                                   rms_calc_right_span.location)
        vals = [fwhm, rms, phase_angle, current]
        vals_formatted = [length_output(v) for v in vals]
        table_data = dict(
            quantities=["FWHM length, cm", "RMS length, cm",
                        "Phase angle, deg.", "Current, mA"],
            values=vals_formatted)
        table_source.data = table_data
        data_logging.add_record((fwhm, rms, rms_calc_left_span.location,
                                 rms_calc_right_span.location,
                                 cutoff_slider.value, phase_angle,
                                 current))
        acnet_logger.send_to_ACNET(fwhm, rms)
        reconstructed_line_source.data = dict(x=bpm.time_arr,
                                              y=reconstructed_signal)
        oscilloscope_line_source.data = dict(x=bpm.time_arr,
                                             y=original_signal)
        plot.title.text = "Last updated: {}".format(datetime.datetime.now())
        if toggle.active:
            vs = check_if_need_update_vertical_span(original_signal)
            print("vs = ", vs)
            if vs == 1:
                button_increase_callback(1)
            elif vs == -1:
                button_decrease_callback(1)
        else:
            if toggle_increase.active:
                print("Increase active")
                button_increase_callback(1)
                toggle_increase.active = False
            if toggle_decrease.active:
                button_decrease_callback(1)
                toggle_decrease.active = False
    except Exception as e:
        print("Exception happened in try_update_plot:", e)


curdoc().add_periodic_callback(try_update_plot, 500)
