import socket
import re
import numpy as np
from server_modules.config_requests import get_from_config
import time
import pandas as pd
import os
import time
from server_modules.lecroy import LeCroyScope


class ConnectionToScope():
    timeout = 5  # sec
    HOST = get_from_config("oscilloscope_ip")
    PORT = get_from_config("oscilloscope_port")
    wcm_channel = 3
    rf_channel=2
    command_panel_setup = b'\x81\x01\x00\x00\x00\x00\x00\x08CORD'\
        b' LO\n\x81\x01\x00\x00\x00\x00\x00\x08 *RCL 4\n'

    def __init__(self, dt_ns, testing=False):
        self.dt = dt_ns
        self.testing = testing
        self.scope = LeCroyScope(self.HOST, timeout=self.timeout)
        nsequence = 1
        self.scope.clear()
        self.scope.set_sequence_mode(nsequence)
        settings = self.scope.get_settings()
        if b'ON' in settings['SEQUENCE']:
            sequence_count = int(settings['SEQUENCE'].split(',')[1])
        else:
            sequence_count = 1
            
        if nsequence != sequence_count:
            print( 'Could not configure sequence mode properly')
        if sequence_count != 1:
            print( 'Using sequence mode with %i traces per aquisition' % sequence_count )
        self.scope.trigger()



    def get_waveform_generic(self, channel):
        
        desc, array = self.scope.get_waveform(channel)
        # print(desc)
        # print(array)
        return desc['vertical_gain']*array - desc['vertical_offset']

    def get_waveform_testing(self):
        v_arr_data = pd.read_csv(os.path.join(os.getcwd(),
                                              "bunch-profile-monitor",
                                              "signal_transfer_line_data",
                                              "v_arr_test.csv"), header=None)
        v_arr = v_arr_data.values.transpose()[0]
        # random additive here
        v_arr = np.asarray(v_arr)+np.random.uniform(-0.005, 0.005, len(v_arr))
        self.v_arr = v_arr
        return self.v_arr

    def get_waveform(self):
        if self.testing:
            res = self.get_waveform_testing()
        else:
            res = self.get_waveform_generic(self.wcm_channel)
        return res

    def get_waveform_RF_testing(self):
        v_arr_data = pd.read_csv(os.path.join(os.getcwd(),
                                              "bunch-profile-monitor",
                                              "signal_transfer_line_data",
                                              "v_rf_arr_test.csv"),
                                 header=None)
        self.v_arr = v_arr_data.loc[:, 0].values\
            + np.random.uniform(-0.005, 0.005, len(self.v_arr))
        return self.v_arr

    def get_waveform_RF(self):
        if self.testing:
            res = self.get_waveform_RF_testing()
        else:
            res = self.get_waveform_generic(self.rf_channel)
        return res

    def get_generic(self, command):
        self.scope.send(command + '?')
        res = self.scope.recv().strip()
        self.scope.check_last_command()
        return float(res.decode().split()[1])

    def set_generic(self, command, val):
        self.scope.send(f"{command} {val} V")
        self.scope.check_last_command()
        time.sleep(0.25)

    

    def get_volt_div(self):
        return self.get_generic(f"C{self.wcm_channel}:VOLT_DIV")

    def set_volt_div(self, volt_div):
        self.set_generic(f"C{self.wcm_channel}:VOLT_DIV", volt_div)

    def get_offset(self):
        return self.get_generic(f"C{self.wcm_channel}:OFFSET")

    def set_offset(self, offset):
        self.set_generic(f"C{self.wcm_channel}:OFFSET", offset)

    def set_panel_settings(self):
        self.scope.send("*RCL 4")
        self.scope.check_last_command()
        time.sleep(1)



if __name__ == "__main__":
    conn = ConnectionToScope()
    v_arr = conn.get_waveform()
