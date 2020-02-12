import sqlite3
import os
conn = sqlite3.connect(os.path.join(os.getcwd(),
                       "bunch-profile-monitor", "log.db"))
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE log
            (date text, FWHM real, RMS real)''')
conn.commit()
conn.close()
