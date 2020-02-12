import webbrowser
import os
from config_requests import get_from_config


def on_server_loaded(server_context):
    ''' If present, this function is called when the server first starts. '''
    if not os.path.exists(os.path.join(os.getcwd(),
                          "bunch-profile-monitor", "log.db")):
        exec(open(os.path.join(os.getcwd(),
             "bunch-profile-monitor", "create_db.py")).read())
    webbrowser.open_new(get_from_config("url"))
    os.system("python3 ~/bunch-profile-monitor/redirect_url.py &")
