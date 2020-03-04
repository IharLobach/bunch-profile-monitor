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
    quiery_waveform = b"\x81\x01\x00\x00\x00\x00\x00\x08CORD"\
        b" LO\n\x81\x01\x00\x00\x00\x00\x00\x14 C3:INSPECT? SIMPLE\n"
    quiery_volt_div = b'\x81\x01\x00\x00\x00\x00\x00\x08CORD'\
        b' LO\n\x81\x01\x00\x00\x00\x00\x00\x0e C3:VOLT_DIV?\n'
    quiery_offset = b'\x81\x01\x00\x00\x00\x00\x00\x08CORD'\
        b' LO\n\x81\x01\x00\x00\x00\x00\x00\x0c C3:OFFSET?\n'

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.HOST, self.PORT))

    def get_waveform(self):
        allowed_symbols = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
                           '.', 'e', '+', '-', ' ')
        self.sock.sendall(self.quiery_waveform)
        received = b''
        while True:
            received += self.sock.recv(4096)
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

    def get_volt_div(self):
        self.sock.sendall(self.quiery_volt_div)
        received = b''
        while True:
            received += self.sock.recv(4096)
            if received[-2:] == b'V\n':
                break
        res = float(re.split(b' ', received)[1])
        return res

    def set_volt_div(self, volt_div):
        command_volt_div = b'\x81\x01\x00\x00\x00\x00\x00\x08CORD'\
            b' LO\n\x81\x01\x00\x00\x00\x00\x00\x13'\
            b' C3:VOLT_DIV ' + \
            '{}'.format(volt_div).encode()+b' V\n'
        # print(command_volt_div)
        self.sock.sendall(command_volt_div)
        time.sleep(0.5)

    def get_offset(self):
        self.sock.sendall(self.quiery_offset)
        received = b''
        while True:
            received += self.sock.recv(4096)
            if received[-2:] == b'V\n':
                break
        res = float(re.split(b' ', received)[1])
        return res
    
    def close(self):
        self.sock.close()


if __name__ == "__main__":
    conn = ConnectionToScope()
    v_arr = conn.get_waveform()
