import sqlite3
import os


def create_db():
    conn = sqlite3.connect(os.path.join(os.getcwd(),
                           "bunch-profile-monitor", "log.db"))
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE log
                (date text, FWHM real, RMS real, BunchPhase real,
                Current real, RFAmpl real, RFPhase real, FUR real,
                LeftLim real, RightLim real, CutOff real)''')
    conn.commit()
    conn.close()
