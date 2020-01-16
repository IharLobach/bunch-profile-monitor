import socket
import re
import numpy as np

class ConnectionToScope():
    timeout = 1#sec
    HOST, PORT = "131.225.118.120", 1861
    quiery_id = b"\x81\x01\x00\x00\x00\x00\x00\x08CORD LO\n\x81\x01\x00\x00\x00\x00\x00\x07 *IDN?"
    quiery_waveform = b"\x81\x01\x00\x00\x00\x00\x00\x08CORD LO\n\x81\x01\x00\x00\x00\x00\x00\x14 C4:INSPECT? SIMPLE"
    def get_waveform(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(self.timeout)
            sock.connect((self.HOST, self.PORT))
            sock.sendall(self.quiery_waveform)
            received = b''
            while True:
                received += sock.recv(4096)
                if received[-4:] == b'\r\n"\n':  # if end of message
                    break
            received1 = received.split(b'INSP')[1]
            received2 = []
            for b in received1:
                c = chr(b)
                if c in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', 'e', '+', '-', ' '):
                    received2.append(b)
            received3 = bytes(received2).strip()
            numbers = re.split(b'\s{1,2}', received3)
            v_arr = np.asarray([float(v) for v in numbers])
            # for now let's assume the time interval between samples is 0.2 ns
            # delta_t = 0.2
            # time_arr = delta_t * np.arange(len(v_arr))
            return v_arr

if __name__=="__main__":
    conn = ConnectionToScope()
    v_arr = conn.get_waveform()