import webbrowser
import os
from server_modules.config_requests import get_from_config
from server_modules.create_db import create_db


def on_server_loaded(server_context):
    ''' If present, this function is called when the server first starts. '''
    if not os.path.exists(os.path.join(os.getcwd(),
                          "bunch-profile-monitor", "log.db")):
        create_db()
    webbrowser.open_new(get_from_config("url"))
    os.system("python3 ~/bunch-profile-monitor/redirect_url.py &")
