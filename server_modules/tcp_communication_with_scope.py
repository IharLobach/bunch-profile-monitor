import socket
import re
import numpy as np
from server_modules.config_requests import get_from_config
import time


class ConnectionToScope():
    timeout = 1  # sec
    HOST = get_from_config("oscilloscope_ip")
    PORT = get_from_config("oscilloscope_port")
    quiery_id = b"\x81\x01\x00\x00\x00\x00\x00\x08CORD"\
                b" LO\n\x81\x01\x00\x00\x00\x00\x00\x07 *IDN?\n"
    quiery_waveform_WCM = b"\x81\x01\x00\x00\x00\x00\x00\x08CORD"\
        b" LO\n\x81\x01\x00\x00\x00\x00\x00\x14 C3:INSPECT? SIMPLE\n"
    quiery_waveform_RF_probe = b"\x81\x01\x00\x00\x00\x00\x00\x08CORD"\
        b" LO\n\x81\x01\x00\x00\x00\x00\x00\x14 C2:INSPECT? SIMPLE\n"
    quiery_volt_div = b'\x81\x01\x00\x00\x00\x00\x00\x08CORD'\
        b' LO\n\x81\x01\x00\x00\x00\x00\x00\x0e C3:VOLT_DIV?\n'
    quiery_offset = b'\x81\x01\x00\x00\x00\x00\x00\x08CORD'\
        b' LO\n\x81\x01\x00\x00\x00\x00\x00\x0c C3:OFFSET?\n'

    def get_waveform_generic(self, quiery):
        allowed_symbols = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                           '.', 'e', '+', '-', ' ')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            while True:
                try:
                    sock.connect((self.HOST, self.PORT))
                    break
                except Exception as e:
                    pass  # print(e)
            sock.sendall(quiery)
            received = b''
            while True:
                received += sock.recv(4096)
                if received[-4:] == b'\r\n"\n':  # if end of message
                    break
            received1 = received.split(b'INSP')[1]
            received2 = []
            for b in received1:
                c = chr(b)
                if c in allowed_symbols:
                    received2.append(b)
            received3 = bytes(received2).strip()
            numbers = re.split(b'\s{1,2}', received3)
            v_arr = np.asarray([float(v) for v in numbers])
            return v_arr

    def get_waveform(self):
        return self.get_waveform_generic(self.quiery_waveform_WCM)

    def get_waveform_RF(self):
        return self.get_waveform_generic(self.quiery_waveform_RF_probe)

    def get_volt_div(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            while True:
                try:
                    sock.connect((self.HOST, self.PORT))
                    break
                except Exception as e:
                    pass  # print(e)
            sock.sendall(self.quiery_volt_div)
            received = b''
            while True:
                received += sock.recv(4096)
                if received[-2:] == b'V\n':
                    break
            res = float(re.split(b' ', received)[1])
            return res

    def set_volt_div(self, volt_div):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            while True:
                try:
                    sock.connect((self.HOST, self.PORT))
                    break
                except Exception as e:
                    pass#print(e)
            command_volt_div = b'\x81\x01\x00\x00\x00\x00\x00\x08CORD'\
                b' LO\n\x81\x01\x00\x00\x00\x00\x00\x13'\
                b' C3:VOLT_DIV ' + \
                '{}'.format(volt_div).encode()+b' V\n'
            # print(command_volt_div)
            sock.sendall(command_volt_div)
            time.sleep(0.25)

    def get_offset(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            while True:
                try:
                    sock.connect((self.HOST, self.PORT))
                    break
                except Exception as e:
                    pass #  print(e)
            sock.sendall(self.quiery_offset)
            received = b''
            while True:
                received += sock.recv(4096)
                if received[-2:] == b'V\n':
                    break
            res = float(re.split(b' ', received)[1])
            return res

    def set_offset(self, offset):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            while True:
                try:
                    sock.connect((self.HOST, self.PORT))
                    break
                except Exception as e:
                    pass  # print(e)
            command_offset = b'\x81\x01\x00\x00\x00\x00\x00\x08CORD'\
                b' LO\n\x81\x01\x00\x00\x00\x00\x00\x13'\
                b' C3:OFFSET ' + \
                '{}'.format(offset).encode()+b' V\n'
            # print(command_offset)
            sock.sendall(command_offset)
            time.sleep(0.25)


if __name__ == "__main__":
    conn = ConnectionToScope()
    v_arr = conn.get_waveform()
