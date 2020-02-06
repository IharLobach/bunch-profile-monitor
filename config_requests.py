import json
def get_from_config(name):
    with open("bunch-profile-monitor/config.json") as f:
            val = json.load(f)[name]
    return val