import os
from flask import Flask, redirect
from config_requests import get_from_config

app = Flask(__name__)


@app.route('/')
def hello():
    return redirect(get_from_config("url"), code=302)


if __name__ == '__main__':
    # default port is 5000
    app.run(host='0.0.0.0')
