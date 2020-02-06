import webbrowser
from config_requests import get_from_config
def on_server_loaded(server_context):
    ''' If present, this function is called when the server first starts. '''
    webbrowser.open_new(get_from_config("url"))