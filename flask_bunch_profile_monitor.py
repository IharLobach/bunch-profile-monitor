from flask import Flask, render_template

from bokeh.client import pull_session
from bokeh.embed import server_session

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    # generate a script to load the customized session
    script = server_session(session_id="514", url='http://localhost:5006/bokeh_gui')

    # use the script in the rendered page
    return render_template("index.html", script=script, template="Flask")

if __name__ == '__main__':
    app.run(port=8080,debug=True)