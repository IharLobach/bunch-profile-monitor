import os
import socket
from datetime import datetime
import sys
UDP_IP = "131.225.120.60"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

while True:
    try:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        vals = data.split('|')
        parsed_vals = [0 if v=="NaN" else float(v) for v in vals]
        fwhm,rms,bunch_phase,current,rf_ampl,rf_phase,fur,mad,rmsg,currentg = parsed_vals
        os.system('acl "enable settings;disable setLogging;set N:IWCMBF '+str(fwhm)+
        ';set N:IWCMBR '+str(rms)+ ';set N:IWCMBP '+str(bunch_phase)+';set N:IWCMI '
        +str(current)+';set N:IRFEPA '+str(rf_ampl)+';set N:IRFEPP '+str(rf_phase)
        +';set N:IWCMBE '+str(fur)+';set N:IWCMBM '+str(mad)+';set N:IWCMBG '+str(rmsg)
        +';set N:IWCMIG '+str(currentg)+'"')
    except Exception as e:
        print datetime.now(), ": some error happened:", e
        #sys.exit(0)