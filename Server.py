#!/usr/bin/python3

import flask
import os

app = flask.Flask(__name__)
# Uncomment this line to force cookies to expire
# every time the application is restarted
#app.secret_key = os.urandom(32)


@app.before_first_request
def onstart():
    # Use this function to initialize modules and global vars
    pass


@app.route('/', methods=['GET'])
def rootdir():
    # This is a good place to start
    message = "I'm a webpage... Probably"
    return flask.render_template('root.html', **locals())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, debug=True)
